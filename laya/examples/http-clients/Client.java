/* Laya 决策服务的外部客户端（Java 8 兼容，等价于 JDK 8 写法：HttpURLConnection + 手拼 JSON）。
 *
 * 为什么不用 java.net.http.HttpClient：那是 JDK 11+ 才有的 API，
 * 我们的项目口径统一在 JDK 1.8 + Spring Boot 2.7，所以这里用 HttpURLConnection。
 *
 * 编译与运行（本机用 JDK 21，按 release 8 编译以证明 JDK 8 也能用）：
 *     javac --release 8 -d /tmp/laya-client Client.java
 *     LAYA_API_KEY=... java -cp /tmp/laya-client Client http://192.168.1.167:8077 "请把 3 月的账单退款"
 *
 * 放进 Spring Boot 项目时：把 call() 里的三步（开连接 / 写 body / 读响应）搬到
 * RestTemplate 或 HttpURLConnection 的工具类里即可；响应体直接用 Jackson 反序列化成 Map。
 */
import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.Charset;

public class Client {

    private static final Charset UTF8 = Charset.forName("UTF-8");

    public static String call(String baseUrl, String text, String apiKey) throws Exception {
        URL url = new URL(baseUrl.replaceAll("/+$", "") + "/decide");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        try {
            conn.setRequestMethod("POST");
            conn.setConnectTimeout(5000);
            conn.setReadTimeout(60000);          // 首次请求可能慢一个数量级，读超时别设太紧
            conn.setDoOutput(true);
            conn.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
            if (apiKey != null && apiKey.length() > 0) {
                conn.setRequestProperty("X-API-Key", apiKey);
            }

            String body = "{\"state\":{\"message\":\"" + escape(text) + "\"}}";
            OutputStream os = conn.getOutputStream();
            try {
                os.write(body.getBytes(UTF8));
            } finally {
                os.close();
            }

            int code = conn.getResponseCode();
            InputStream is = (code >= 200 && code < 300) ? conn.getInputStream() : conn.getErrorStream();
            String resp = read(is);
            if (code != 200) {
                throw new IllegalStateException("HTTP " + code + ": " + resp);
            }
            return resp;
        } finally {
            conn.disconnect();
        }
    }

    private static String read(InputStream is) throws Exception {
        if (is == null) {
            return "";
        }
        StringBuilder sb = new StringBuilder();
        BufferedReader br = new BufferedReader(new InputStreamReader(is, UTF8));
        try {
            String line;
            while ((line = br.readLine()) != null) {
                sb.append(line);
            }
        } finally {
            br.close();
        }
        return sb.toString();
    }

    /** 最小 JSON 字符串转义：够用即可，生产环境请用 Jackson 序列化。 */
    private static String escape(String s) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c == '"' || c == '\\') {
                sb.append('\\').append(c);
            } else if (c == '\n') {
                sb.append("\\n");
            } else if (c == '\r') {
                sb.append("\\r");
            } else if (c == '\t') {
                sb.append("\\t");
            } else if (c < 0x20) {
                sb.append(String.format("\\u%04x", (int) c));
            } else {
                sb.append(c);
            }
        }
        return sb.toString();
    }

    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.err.println("用法: java Client <baseUrl> <text>");
            System.err.println("      java Client http://192.168.1.167:8077 \"请把 3 月的账单退款\"");
            System.exit(1);
        }
        String baseUrl = args[0];
        String text = args[1];
        String key = System.getenv("LAYA_API_KEY");

        long t0 = System.currentTimeMillis();
        String resp = call(baseUrl, text, key);
        long cost = System.currentTimeMillis() - t0;

        System.out.println("HTTP 响应（" + cost + " ms，含网络往返）:");
        System.out.println(resp);
    }
}
