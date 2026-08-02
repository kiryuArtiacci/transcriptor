package com.transcriptor.model;

public record Segment(
    double start,
    double end,
    String text,
    int speakerId
) {}
