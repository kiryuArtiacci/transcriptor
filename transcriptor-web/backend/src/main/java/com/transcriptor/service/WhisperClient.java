package com.transcriptor.service;

import com.transcriptor.model.Segment;
import com.transcriptor.model.TranscriptionResult;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.client.HttpStatusCodeException;

import java.io.File;
import java.util.ArrayList;
import java.util.List;

@Service
public class WhisperClient {

    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;
    private final String serviceUrl;

    public WhisperClient(@Value("${whisper.service.url}") String serviceUrl) {
        this.restTemplate = new RestTemplate();
        this.objectMapper = new ObjectMapper();
        this.serviceUrl = serviceUrl;
    }

    public TranscriptionResult transcribe(File audioFile, String language, boolean diarize) {
        var headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("file", new FileSystemResource(audioFile));
        body.add("language", language);
        body.add("diarize", String.valueOf(diarize));

        var request = new HttpEntity<>(body, headers);
        try {
            var response = restTemplate.postForEntity(
                    serviceUrl + "/transcribe", request, JsonNode.class);
            return parseResult(response.getBody());
        } catch (HttpStatusCodeException e) {
            return new TranscriptionResult(
                    "Error del motor de transcripción: " + e.getResponseBodyAsString(),
                    List.of(), "", 0, "error", 0);
        } catch (Exception e) {
            return new TranscriptionResult(
                    "No se pudo conectar al motor de transcripción: " + e.getMessage(),
                    List.of(), "", 0, "error", 0);
        }
    }

    public TranscriptionResult transcribeGoogle(File audioFile, String language) {
        var headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("file", new FileSystemResource(audioFile));
        body.add("language", language);

        var request = new HttpEntity<>(body, headers);
        try {
            var response = restTemplate.postForEntity(
                    serviceUrl + "/transcribe-google", request, JsonNode.class);
            return parseResult(response.getBody());
        } catch (HttpStatusCodeException e) {
            return new TranscriptionResult(
                    "Error del motor de transcripción: " + e.getResponseBodyAsString(),
                    List.of(), "", 0, "error", 0);
        } catch (Exception e) {
            return new TranscriptionResult(
                    "No se pudo conectar al motor de transcripción: " + e.getMessage(),
                    List.of(), "", 0, "error", 0);
        }
    }

    private TranscriptionResult parseResult(JsonNode node) {
        if (node == null || node.has("error")) {
            var err = node != null ? node.get("error").asText() : "unknown";
            return new TranscriptionResult("Error: " + err, List.of(), "", 0, "error", 0);
        }

        List<Segment> segments = new ArrayList<>();
        if (node.has("segments")) {
            for (JsonNode seg : node.get("segments")) {
                segments.add(new Segment(
                        seg.get("start").asDouble(),
                        seg.get("end").asDouble(),
                        seg.get("text").asText(),
                        seg.has("speaker_id") ? seg.get("speaker_id").asInt() : 0
                ));
            }
        }

        return new TranscriptionResult(
                node.get("full_text").asText(),
                segments,
                node.get("language").asText(),
                node.get("duration").asDouble(),
                node.get("backend").asText(),
                node.has("speakers_detected") ? node.get("speakers_detected").asInt() : 0
        );
    }
}
