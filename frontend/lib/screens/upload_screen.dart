import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import '../services/api_service.dart';
import 'result_screen.dart';

class UploadScreen extends StatefulWidget {
  @override
  _UploadScreenState createState() => _UploadScreenState();
}

class _UploadScreenState extends State<UploadScreen> {
  bool loading = false;
  String? fileName; // Store the selected file name

  Future<void> uploadFile() async {
    FilePickerResult? result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf', 'doc', 'docx'],
    );

    if (result == null) return;

    setState(() {
      fileName = result.files.single.name;
      loading = true;
    });

    String path = result.files.single.path!;

    try {
      var response = await ApiService.uploadContract(path);

      print("BACKEND RESPONSE:");
      print(response);

      if (mounted) {
        setState(() {
          loading = false;
        });

        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => ResultScreen(data: response),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          loading = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Upload failed: $e")),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: Text("Car Lease AI", style: TextStyle(fontWeight: FontWeight.bold)),
        centerTitle: true,
        elevation: 0,
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Header Illustration/Icon
            Icon(Icons.description_outlined, size: 80, color: Colors.blue[800]),
            SizedBox(height: 24),
            Text(
              "Analyze Your Lease",
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 8),
            Text(
              "Upload your contract PDF to get a risk assessment and AI-powered advice.",
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.grey[600], fontSize: 16),
            ),
            SizedBox(height: 40),

            // FIXED: File Name Display Bar
            if (fileName != null)
              Container(
                margin: EdgeInsets.only(bottom: 20), // Fixed the EdgeInsets error here
                padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                decoration: BoxDecoration(
                  color: Colors.blue.withOpacity(0.05),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.blue.withOpacity(0.2)),
                ),
                child: Row(
                  children: [
                    Icon(Icons.insert_drive_file, color: Colors.blue[800]),
                    SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        fileName!,
                        style: TextStyle(fontWeight: FontWeight.w500),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    if (loading)
                      SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.blue[800]),
                      )
                    else
                      Icon(Icons.check_circle, color: Colors.green),
                  ],
                ),
              ),

            // Upload Button
            SizedBox(
              width: double.infinity,
              height: 56,
              child: ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue[800],
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                  elevation: 2,
                ),
                onPressed: loading ? null : uploadFile,
                icon: loading
                    ? SizedBox.shrink()
                    : Icon(Icons.cloud_upload_outlined),
                label: Text(
                  loading ? "ANALYZING CONTRACT..." : "UPLOAD LEASE CONTRACT",
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, letterSpacing: 1),
                ),
              ),
            ),

            if (loading)
              Padding(
                padding: const EdgeInsets.only(top: 16.0),
                child: Text(
                  "Our AI is reading your document...",
                  style: TextStyle(fontStyle: FontStyle.italic, color: Colors.grey[600]),
                ),
              ),
          ],
        ),
      ),
    );
  }
}