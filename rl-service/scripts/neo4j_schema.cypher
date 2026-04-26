CREATE CONSTRAINT paper_aminer_id IF NOT EXISTS
FOR (p:Paper) REQUIRE p.aminer_id IS UNIQUE;

CREATE CONSTRAINT author_author_id IF NOT EXISTS
FOR (a:Author) REQUIRE a.author_id IS UNIQUE;

CREATE CONSTRAINT keyword_keyword_id IF NOT EXISTS
FOR (k:Keyword) REQUIRE k.keyword_id IS UNIQUE;

CREATE CONSTRAINT venue_venue_id IF NOT EXISTS
FOR (v:Venue) REQUIRE v.venue_id IS UNIQUE;

CREATE CONSTRAINT graph_node_id IF NOT EXISTS
FOR (n:GraphNode) REQUIRE n.node_id IS UNIQUE;

CREATE INDEX paper_title IF NOT EXISTS
FOR (p:Paper) ON (p.title);

CREATE INDEX paper_year IF NOT EXISTS
FOR (p:Paper) ON (p.year);

CREATE INDEX paper_citation_count IF NOT EXISTS
FOR (p:Paper) ON (p.citation_count);

CREATE INDEX author_name IF NOT EXISTS
FOR (a:Author) ON (a.name);
