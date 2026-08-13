package com.transcriptor.service;

import com.transcriptor.model.TranscriptionResult;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;

@Service
public class TranscriptionService {

    private final WhisperClient whisperClient;

    public TranscriptionService(WhisperClient whisperClient) {
        this.whisperClient = whisperClient;
    }

    public TranscriptionResult transcribeFile(MultipartFile file, String language, boolean diarize) throws Exception {
        Path temp = Files.createTempFile("transcriptor_", extensionOf(file));
        try {
            file.transferTo(temp.toFile());
            return whisperClient.transcribe(temp.toFile(), language, diarize);
        } finally {
            temp.toFile().delete();
        }
    }

    public TranscriptionResult transcribeLive(MultipartFile file, String language, boolean diarize) throws Exception {
        Path temp = Files.createTempFile("transcriptor_live_", extensionOf(file));
        try {
            file.transferTo(temp.toFile());
            return transcribeLive(temp.toFile(), language, diarize);
        } finally {
            temp.toFile().delete();
        }
    }

    public TranscriptionResult transcribeLive(File audioFile, String language, boolean diarize) {
        if (diarize) {
            return whisperClient.transcribe(audioFile, language, true);
        }
        return whisperClient.transcribeGoogle(audioFile, language);
    }

    private static String extensionOf(MultipartFile file) {
        String name = file.getOriginalFilename();
        if (name != null && name.contains(".")) {
            return name.substring(name.lastIndexOf('.'));
        }
        return ".wav";
    }
}
