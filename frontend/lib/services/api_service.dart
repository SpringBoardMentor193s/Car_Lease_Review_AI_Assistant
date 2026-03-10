import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {

  static const String baseUrl = "http://10.145.148.70:8000";

  static Future<Map<String, dynamic>> uploadContract(String filePath) async {

    var request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl/upload'),
    );

    request.files.add(
      await http.MultipartFile.fromPath('file', filePath),
    );

    var response = await request.send();
    var responseBody = await response.stream.bytesToString();

    return jsonDecode(responseBody);
  }

  static Future<Map<String, dynamic>> negotiate(
      String contractId, String message) async {

    final response = await http.post(
      Uri.parse('$baseUrl/negotiate'),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({
        "contract_id": int.parse(contractId), // FIX
        "user_message": message               // FIX
      }),
    );

    return jsonDecode(response.body);
  }
}