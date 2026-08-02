package com.transcriptor.controller;

import com.transcriptor.service.TranscriptionService;
import com.fasterxml.jackson.databind.ObjectMapper;

import org.springframework.stereotype.Component;
import org.springframework.web.socket.BinaryMessage;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.AbstractWebSocketHandler;

import java.io.File;
import java.nio.ByteBuffer;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Component
public class WebSocketController extends AbstractWebSocketHandler {

    private final TranscriptionService service;
    private final ObjectMapper mapper = new ObjectMapper();
    private final Map<String, List<byte[]>> sessionBuffers = new java.util.concurrent.ConcurrentHashMap<>();

    public WebSocketController(TranscriptionService service) {
        this.service = service;
    }

    @Override
    public void handleBinaryMessage(WebSocketSession session, BinaryMessage message) throws Exception {
        ByteBuffer buffer = message.getPayload();
        byte[] chunk = new byte[buffer.remaining()];
        buffer.get(chunk);

        sessionBuffers.computeIfAbsent(session.getId(), k -> new ArrayList<>()).add(chunk);
        session.sendMessage(new TextMessage("{\"type\":\"chunk_received\"}"));
    }

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        var node = mapper.readTree(message.getPayload());
        String type = node.get("type").asText();

        if ("finalize".equals(type)) {
            String language = node.has("language") ? node.get("language").asText() : "es";
            boolean diarize = node.has("diarize") && node.get("diarize").asBoolean();

            var chunks = sessionBuffers.remove(session.getId());
            if (chunks == null || chunks.isEmpty()) {
                session.sendMessage(new TextMessage(
                        "{\"type\":\"error\",\"text\":\"No audio captured\"}"));
                return;
            }

            Path temp = Files.createTempFile("websocket_rec_", ".wav");
            try {
                writeWav(temp, chunks);
                var result = service.transcribeLive(temp.toFile(), language, diarize);
                var json = mapper.writeValueAsString(Map.of(
                        "type", "final",
                        "fullText", result.fullText(),
                        "segments", result.segments(),
                        "speakersDetected", result.speakersDetected(),
                        "backend", result.backend(),
                        "duration", result.duration()
                ));
                session.sendMessage(new TextMessage(json));
            } finally {
                temp.toFile().delete();
            }
        }
    }

    private void writeWav(Path path, List<byte[]> chunks) throws Exception {
        var out = Files.newOutputStream(path);
        out.write(wavHeader(chunks.size()));
        for (byte[] chunk : chunks) {
            out.write(chunk);
        }
        out.close();
    }

    private byte[] wavHeader(int totalChunks) {
        int dataSize = 0;
        int sampleRate = 16000;
        int sampleWidth = 2;
        var header = new byte[44];

        header[0] = 'R'; header[1] = 'I'; header[2] = 'F'; header[3] = 'F';
        header[8] = 'W'; header[9] = 'A'; header[10] = 'V'; header[11] = 'E';
        header[12] = 'f'; header[13] = 'm'; header[14] = 't'; header[15] = ' ';
        header[16] = 16; header[17] = 0; header[18] = 0; header[19] = 0;
        header[20] = 1; header[21] = 0;
        header[22] = 1; header[23] = 0;
        header[24] = (byte) (sampleRate & 0xFF);
        header[25] = (byte) ((sampleRate >> 8) & 0xFF);
        header[26] = (byte) ((sampleRate >> 16) & 0xFF);
        header[27] = (byte) ((sampleRate >> 24) & 0xFF);
        int byteRate = sampleRate * sampleWidth;
        header[28] = (byte) (byteRate & 0xFF);
        header[29] = (byte) ((byteRate >> 8) & 0xFF);
        header[30] = (byte) ((byteRate >> 16) & 0xFF);
        header[31] = (byte) ((byteRate >> 24) & 0xFF);
        header[32] = (byte) sampleWidth; header[33] = 0;
        header[34] = 16; header[35] = 0;
        header[36] = 'd'; header[37] = 'a'; header[38] = 't'; header[39] = 'a';
        header[40] = (byte) (dataSize & 0xFF);
        header[41] = (byte) ((dataSize >> 8) & 0xFF);
        header[42] = (byte) ((dataSize >> 16) & 0xFF);
        header[43] = (byte) ((dataSize >> 24) & 0xFF);

        return header;
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
        sessionBuffers.remove(session.getId());
    }
}
