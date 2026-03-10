import 'package:flutter/material.dart';
import '../services/api_service.dart';

class NegotiationScreen extends StatefulWidget {
  final String contractId;

  NegotiationScreen({required this.contractId});

  @override
  _NegotiationScreenState createState() => _NegotiationScreenState();
}

class _NegotiationScreenState extends State<NegotiationScreen> {
  TextEditingController controller = TextEditingController();
  String lastUserMessage = ""; // Track user message
  String response = "";
  bool loading = false;

  void sendMessage() async {
    if (controller.text.isEmpty) return;

    setState(() {
      lastUserMessage = controller.text;
      loading = true;
      response = ""; // Clear old response for new interaction
    });

    String userText = controller.text;
    controller.clear();

    var res = await ApiService.negotiate(widget.contractId, userText);

    print("NEGOTIATION RESPONSE:");
    print(res);

    if (mounted) {
      setState(() {
        response = res["assistant_reply"] ?? "No response from AI";
        loading = false;
      });
    }
  }

  // UI Widget for Chat Bubbles
  Widget chatBubble(String text, bool isUser) {
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: EdgeInsets.symmetric(vertical: 8),
        padding: EdgeInsets.all(14),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
        decoration: BoxDecoration(
          color: isUser ? Colors.blue[800] : Colors.grey[200],
          borderRadius: BorderRadius.only(
            topLeft: Radius.circular(16),
            topRight: Radius.circular(16),
            bottomLeft: isUser ? Radius.circular(16) : Radius.circular(0),
            bottomRight: isUser ? Radius.circular(0) : Radius.circular(16),
          ),
        ),
        child: Text(
          text,
          style: TextStyle(
            color: isUser ? Colors.white : Colors.black87,
            fontSize: 15,
            height: 1.4,
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Text("Negotiation Assistant", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
            Text("Powered by AI", style: TextStyle(fontSize: 12, color: Colors.blue[200])),
          ],
        ),
        centerTitle: true,
        elevation: 0,
        backgroundColor: Colors.blue[900],
        foregroundColor: Colors.white,
      ),
      body: Column(
        children: [
          // Chat History Area
          Expanded(
            child: ListView(
              padding: EdgeInsets.all(16),
              children: [
                if (lastUserMessage.isNotEmpty) chatBubble(lastUserMessage, true),
                if (loading)
                  Align(
                    alignment: Alignment.centerLeft,
                    child: Padding(
                      padding: const EdgeInsets.all(8.0),
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                  ),
                if (response.isNotEmpty) chatBubble(response, false),
                if (lastUserMessage.isEmpty && !loading)
                  Center(
                    child: Padding(
                      padding: const EdgeInsets.only(top: 100),
                      child: Column(
                        children: [
                          Icon(Icons.chat_bubble_outline, size: 60, color: Colors.grey[300]),
                          SizedBox(height: 12),
                          Text("Ask me anything about your contract",
                              style: TextStyle(color: Colors.grey[500])),
                        ],
                      ),
                    ),
                  )
              ],
            ),
          ),

          // Input Bar Area
          Container(
            padding: EdgeInsets.symmetric(horizontal: 12, vertical: 12),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(color: Colors.black12, blurRadius: 4, offset: Offset(0, -2))
              ],
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: controller,
                    maxLines: null,
                    decoration: InputDecoration(
                      hintText: "Type your question...",
                      hintStyle: TextStyle(color: Colors.grey[400]),
                      filled: true,
                      fillColor: Colors.grey[100],
                      contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(24),
                        borderSide: BorderSide.none,
                      ),
                    ),
                  ),
                ),
                SizedBox(width: 8),
                GestureDetector(
                  onTap: loading ? null : sendMessage,
                  child: CircleAvatar(
                    backgroundColor: loading ? Colors.grey : Colors.blue[800],
                    radius: 24,
                    child: Icon(Icons.send, color: Colors.white, size: 20),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}