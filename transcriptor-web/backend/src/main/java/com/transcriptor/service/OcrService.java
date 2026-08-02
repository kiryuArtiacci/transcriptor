package com.transcriptor.service;

import com.transcriptor.model.OcrResult;
import net.sourceforge.tess4j.Tesseract;
import net.sourceforge.tess4j.TesseractException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.File;

@Service
public class OcrService {

    @Value("${tesseract.datapath}")
    private String tessdataPath;

    public OcrResult extractText(File imageFile, String language) {
        Tesseract tesseract = new Tesseract();
        tesseract.setDatapath(tessdataPath);
        tesseract.setLanguage(language);

        try {
            BufferedImage img = ImageIO.read(imageFile);
            if (img == null) {
                return new OcrResult("No se pudo leer la imagen.");
            }
            String text = tesseract.doOCR(img);
            return new OcrResult(text != null ? text.trim() : "");
        } catch (TesseractException e) {
            return new OcrResult("Error de OCR: " + e.getMessage());
        } catch (Exception e) {
            return new OcrResult("Error: " + e.getMessage());
        }
    }
}
