import 'package:flutter/material.dart';
import 'screens/upload_screen.dart';

void main() {
  runApp(CarLeaseAIApp());
}

class CarLeaseAIApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Car Lease AI',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: UploadScreen(),
    );
  }
}