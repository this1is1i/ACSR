import os
import tempfile
import unittest
import importlib
from unittest.mock import patch

import train as train_module
import agent as agent_module
import scripts.migrate_to_neo4j as migrate_to_neo4j_module
import scripts.backfill_mysql_shadow_papers as backfill_mysql_shadow_papers_module
from agent import ActorCriticAgent
from config import Config
import config as config_module
from knowledge_graph.graph_storage import GraphStorage
from train import train


class RuntimeFixesTest(unittest.TestCase):
    def test_load_model_accepts_checkpoint_saved_with_config_object(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = os.path.join(temp_dir, "ac_model.pth")
            config = Config(
                use_kg=False,
                model_save_path=model_path,
                log_dir=os.path.join(temp_dir, "logs"),
            )
            saver = ActorCriticAgent(config)
            saver.train_step = 7
            saver.episode_count = 3
            saver.save_model()

            loader = ActorCriticAgent(config)

            original_torch_load = agent_module.torch.load

            def strict_load(*args, **kwargs):
                if kwargs.get("weights_only") is False:
                    return original_torch_load(*args, **kwargs)
                raise RuntimeError(
                    "Weights only load failed. Unsupported global: GLOBAL config.Config"
                )

            with patch.object(agent_module.torch, "load", side_effect=strict_load):
                loader.load_model()

            self.assertEqual(loader.train_step, 7)
            self.assertEqual(loader.episode_count, 3)

    def test_graph_storage_edge_mapping_falls_back_when_relation_properties_missing(self):
        storage = GraphStorage()

        fallback_edge = storage._edge_from_row({
            "src_id": "paper_1",
            "dst_id": "paper_2",
            "rel_type": "CITE",
            "rel_props": {},
        })
        explicit_edge = storage._edge_from_row({
            "src_id": "paper_3",
            "dst_id": "keyword_1",
            "rel_type": "HAS_KEYWORD",
            "rel_props": {"relation": "has_keyword", "weight": 0.4},
        })

        self.assertEqual(fallback_edge.relation, "CITE")
        self.assertEqual(fallback_edge.weight, 1.0)
        self.assertEqual(explicit_edge.relation, "has_keyword")
        self.assertEqual(explicit_edge.weight, 0.4)

    def test_train_stops_gracefully_and_saves_checkpoint_when_stop_requested(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = os.path.join(temp_dir, "graceful-stop.pth")
            config = Config(
                use_kg=False,
                max_episodes=5,
                max_steps=2,
                model_save_path=model_path,
                log_dir=os.path.join(temp_dir, "logs"),
            )
            controller = train_module.GracefulStopController()
            controller.request_stop("unit test requested stop")

            agent = train(config, stop_controller=controller)

            self.assertTrue(os.path.exists(model_path))
            self.assertEqual(agent.episode_count, 0)

    def test_config_reads_neo4j_settings_from_environment(self):
        env = {
            "REC_GRAPH_BACKEND": "neo4j",
            "GRAPH_NEO4J_URI": "bolt://example.com:7687",
            "GRAPH_NEO4J_USERNAME": "neo4j-user",
            "GRAPH_NEO4J_PASSWORD": "secret-from-env",
            "GRAPH_NEO4J_DATABASE": "graphdb",
        }
        with patch.dict(os.environ, env, clear=False):
            reloaded = importlib.reload(config_module)
            cfg = reloaded.Config()

        self.assertEqual(cfg.graph_backend, "neo4j")
        self.assertEqual(cfg.neo4j_uri, "bolt://example.com:7687")
        self.assertEqual(cfg.neo4j_user, "neo4j-user")
        self.assertEqual(cfg.neo4j_password, "secret-from-env")
        self.assertEqual(cfg.neo4j_database, "graphdb")

    def test_migrate_to_neo4j_defaults_to_existing_aminer_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            os.makedirs(os.path.join(temp_dir, "data", "AMiner"))

            with patch.object(migrate_to_neo4j_module, "ROOT_DIR", temp_dir):
                with patch("sys.argv", ["migrate_to_neo4j.py"]):
                    args = migrate_to_neo4j_module.parse_args()

            self.assertEqual(args.data_dir, os.path.join(temp_dir, "data", "AMiner"))

    def test_backfill_script_exposes_warning_free_paper_query(self):
        self.assertTrue(
            hasattr(backfill_mysql_shadow_papers_module, "build_paper_fetch_query")
        )
        if hasattr(backfill_mysql_shadow_papers_module, "build_paper_fetch_query"):
            query = backfill_mysql_shadow_papers_module.build_paper_fetch_query()
            self.assertIn("p['embedding'] AS embedding", query)
            self.assertNotIn("p.embedding AS embedding", query)


if __name__ == "__main__":
    unittest.main()
