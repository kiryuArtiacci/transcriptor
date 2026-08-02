package com.transcriptor.model;

import java.util.List;

public record TranscriptionResult(
    String fullText,
    List<Segment> segments,
    String language,
    double duration,
    String backend,
    int speakersDetected
) {}
