package com.example.research.graph;

import lombok.Data;

import java.util.List;

@Data
public class GraphPaper {
    private String graphNodeId;
    private String aminerId;
    private String title;
    private String abstractText;
    private List<String> keywords;
    private List<String> authors;
    private String venue;
    private Integer year;
    private Integer citationCount;
    private String embedding;
}
