import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

public class AiService {
    public static String performTradeoffAnalysis(String option1, String option2, String criteria) {
        // Calls the Gemini API to perform a trade-off analysis for PS-01.
        HttpClient client = HttpClient.newHttpClient();
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create("https://api.gemini.com/ps-01/tradeoff-analysis"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(jsonPayload()))
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        return response.body();
    }

    private String jsonPayload() {
        // Create a JSON payload for the trade-off analysis request.
        return "{\"option1\": \"" + option1 + "\", \"option2\": \"" + option2 + "\", \"criteria\": \"" + criteria + "\"}";
    }

    public static String performDesignReview(String documentText) {
        // Calls the Gemini API to perform a design review for PS-02.
        HttpClient client = HttpClient.newHttpClient();
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create("https://api.gemini.com/ps-02/design-review"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(jsonPayload()))
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        return response.body();
    }

    private String jsonPayload() {
        // Create a JSON payload for the design review request.
        return "{\"documentText\": \"" + documentText + "\"}";
    }
}
