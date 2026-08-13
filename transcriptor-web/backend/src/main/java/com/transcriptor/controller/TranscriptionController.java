package com.transcriptor.controller;

import com.transcriptor.model.ErrorResponse;
import com.transcriptor.model.TranscriptionResult;
import com.transcriptor.service.TranscriptionService;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api")
public class TranscriptionController {

    private final TranscriptionService service;

    public TranscriptionController(TranscriptionService service) {
        this.service = service;
    }

    @PostMapping("/transcribe/file")
    public ResponseEntity<?> transcribeFile(
            @RequestParam("file") MultipartFile file,
            @RequestParam(defaultValue = "es") String language,
            @RequestParam(defaultValue = "false") boolean diarize) {

        if (file.isEmpty()) {
            return ResponseEntity.badRequest().body(new ErrorResponse("Archivo vacío"));
        }

        try {
            TranscriptionResult result = service.transcribeFile(file, language, diarize);
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            return ResponseEntity.internalServerError()
                    .body(new ErrorResponse(e.getMessage()));
        }
    }

    @PostMapping("/transcribe/live")
    public ResponseEntity<?> transcribeLive(
            @RequestParam("file") MultipartFile file,
            @RequestParam(defaultValue = "es") String language,
            @RequestParam(defaultValue = "false") boolean diarize) {

        if (file.isEmpty()) {
            return ResponseEntity.badRequest().body(new ErrorResponse("Archivo vacío"));
        }

        try {
            TranscriptionResult result = service.transcribeLive(file, language, diarize);
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            return ResponseEntity.internalServerError()
                    .body(new ErrorResponse(e.getMessage()));
        }
    }

    @GetMapping("/health")
    public ResponseEntity<?> health() {
        return ResponseEntity.ok(java.util.Map.of("status", "ok", "service", "transcriptor-backend"));
    }
}
