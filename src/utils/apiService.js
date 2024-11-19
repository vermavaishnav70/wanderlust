// utils/apiService.js
import { createGroq } from "@ai-sdk/groq";
import { GoogleGenerativeAI } from "@google/generative-ai";
import { generateText } from "ai";
const systemInstruction = `You are an AI assistant for a trip planner application. Your goal is to generate a personalized trip plan based on the user's preferences. Follow these guidelines to generate a clear, actionable, and time-structured itinerary for the user:
    1. Create a trip plan for the specified duration (e.g., 7 days) with a specific destination.
    2. For each day, break down the itinerary into time-based activities (e.g., '09:00 AM: Visit Louvre Museum').
    3. Include at least 4-5 activities per day with specific times.
    4. Ensure the activities are relevant to the user's travel style, budget, and group size.
    5. Keep the tone friendly, informative, and professional.
    6. return the generated trip plan as a JSON object.`;
export const generateContentWithGroq = async (prompt) => {
  try {
    const groq = createGroq({ apiKey: import.meta.env.VITE_GROQ_API_KEY });
      const response = await generateText({
        model: groq("gemma2-9b-it"),
        prompt: prompt,
      });
      console.log( response.text);
    let cleanResponse = response.text
      .replace(/```json|```/g, "") // Remove markdown code fences
      .replace(/"price":\s*Variable/g, '"price": 0') // Replace "Variable" with a fallback
      .trim();
    return JSON.parse(cleanResponse);
  } catch (error) {
    console.error("Groq Error:", error);
    throw error;
  }
};

export const generateContentWithGemini = async (prompt) => {
  try {
    const genAI = new GoogleGenerativeAI(import.meta.env.VITE_GEMINI_API_KEY);
    const model = genAI.getGenerativeModel({
      model: "gemini-1.5-flash",
      systemInstruction,
    });
    const result = await model.generateContent(prompt);
    const cleanResponse = result.response
      .text()
      .replace(/```json|```/g, "")
      .trim();
    return JSON.parse(cleanResponse);
  } catch (error) {
    console.error("Gemini Error:", error);
    throw error;
  }
};
