package com.transcriptor.controller;

import com.transcriptor.model.ErrorResponse;
import com.transcriptor.model.OcrResult;
import com.transcriptor.service.OcrService;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.nio.file.Files;
import java.nio.file.Path;

@RestController
@RequestMapping("/api")
public class OcrController {

    private final OcrService service;

    public OcrController(OcrService service) {
        this.service = service;
    }

    @PostMapping("/ocr")
    public ResponseEntity<?> extractText(
            @RequestParam("file") MultipartFile file,
            @RequestParam(defaultValue = "spa") String language) {

        if (file.isEmpty()) {
            return ResponseEntity.badRequest().body(new ErrorResponse("Archivo vacío"));
        }

        try {
            Path temp = Files.createTempFile("ocr_", ".png");
            file.transferTo(temp.toFile());
            OcrResult result = service.extractText(temp.toFile(), language);
            temp.toFile().delete();
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            return ResponseEntity.internalServerError()
                    .body(new ErrorResponse(e.getMessage()));
        }
    }
}
