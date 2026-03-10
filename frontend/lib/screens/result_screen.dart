import 'package:flutter/material.dart';
import 'package:syncfusion_flutter_gauges/gauges.dart';
import 'negotiation_screen.dart';

class ResultScreen extends StatelessWidget {
  final Map<String, dynamic> data;

  ResultScreen({required this.data});

  // IMPROVED: Added modern container for icons and better spacing
  Widget sectionCard(String title, IconData icon, List<Widget> children) {
    return Card(
      elevation: 2,
      margin: EdgeInsets.only(bottom: 20),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.blue.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(icon, size: 24, color: Colors.blue[800]),
                ),
                SizedBox(width: 12),
                Text(
                  title,
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 0.5,
                  ),
                ),
              ],
            ),
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 12.0),
              child: Divider(color: Colors.grey[200], thickness: 1),
            ),
            ...children
          ],
        ),
      ),
    );
  }

  Widget info(String label, dynamic value) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(fontWeight: FontWeight.w500, color: Colors.grey[700])),
          Flexible(
            child: Text(
              "${value ?? "N/A"}",
              textAlign: TextAlign.right,
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
    );
  }

  Widget bulletList(List list) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: list.map<Widget>((e) {
        return Padding(
          padding: EdgeInsets.symmetric(vertical: 4),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text("• ", style: TextStyle(color: Colors.blue, fontWeight: FontWeight.bold)),
              Expanded(child: Text(e.toString(), style: TextStyle(height: 1.4))),
            ],
          ),
        );
      }).toList(),
    );
  }

  // UPDATED: Scale set to 0-10 to match your data (Score 7 = High)
  Widget riskGauge(String level, dynamic score) {
    double value = double.tryParse(score.toString()) ?? 0.0;

    return SizedBox(
      height: 210,
      child: SfRadialGauge(
        axes: [
          RadialAxis(
            minimum: 0,
            maximum: 10, // FIXED: Now 0-10 range
            interval: 2,
            showLabels: true,
            showTicks: true,
            axisLineStyle: AxisLineStyle(thickness: 0.1, thicknessUnit: GaugeSizeUnit.factor),
            ranges: [
              GaugeRange(startValue: 0, endValue: 3.3, color: Colors.green, startWidth: 12, endWidth: 12),
              GaugeRange(startValue: 3.3, endValue: 6.6, color: Colors.orange, startWidth: 12, endWidth: 12),
              GaugeRange(startValue: 6.6, endValue: 10, color: Colors.red, startWidth: 12, endWidth: 12),
            ],
            pointers: [
              NeedlePointer(
                value: value,
                needleLength: 0.8,
                needleColor: Colors.black87,
                knobStyle: KnobStyle(knobRadius: 0.08, color: Colors.black87),
              )
            ],
            annotations: [
              GaugeAnnotation(
                widget: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      level,
                      style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                    ),
                    Text("$value / 10", style: TextStyle(fontSize: 14, color: Colors.grey)),
                  ],
                ),
                angle: 90,
                positionFactor: 0.8,
              )
            ],
          )
        ],
      ),
    );
  }

  Widget fairnessGauge(double score) {
    return SizedBox(
      height: 210,
      child: SfRadialGauge(
        axes: [
          RadialAxis(
            minimum: 0,
            maximum: 100,
            showLabels: true,
            showTicks: true,
            axisLineStyle: AxisLineStyle(thickness: 0.1, thicknessUnit: GaugeSizeUnit.factor),
            ranges: [
              GaugeRange(startValue: 0, endValue: 40, color: Colors.red, startWidth: 12, endWidth: 12),
              GaugeRange(startValue: 40, endValue: 70, color: Colors.orange, startWidth: 12, endWidth: 12),
              GaugeRange(startValue: 70, endValue: 100, color: Colors.green, startWidth: 12, endWidth: 12),
            ],
            pointers: [
              NeedlePointer(
                value: score,
                needleLength: 0.8,
                needleColor: Colors.black87,
                knobStyle: KnobStyle(knobRadius: 0.08, color: Colors.black87),
              )
            ],
            annotations: [
              GaugeAnnotation(
                widget: Text(
                  "${score.toInt()}%",
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                ),
                angle: 90,
                positionFactor: 0.8,
              )
            ],
          )
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    var vehicle = data["vehicle_data"] ?? {};
    var recall = data["recall_data"] ?? {};
    var sla = data["sla_data"] ?? {};
    var safety = data["safety_rating"] ?? {};
    var risk = data["risk_assessment"] ?? {};
    var fairness = data["fairness_score"] ?? {};
    var summary = data["contract_summary"] ?? {};
    var advice = data["ai_advice"] ?? [];

    return Scaffold(
      backgroundColor: Colors.grey[50], // Light background to make cards pop
      appBar: AppBar(
        title: Text("Contract Analysis", style: TextStyle(fontWeight: FontWeight.bold)),
        centerTitle: true,
        elevation: 0,
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
      ),

      body: SingleChildScrollView(
        padding: EdgeInsets.symmetric(horizontal: 16, vertical: 20),
        child: Column(
          children: [
            sectionCard(
              "Vehicle Information",
              Icons.directions_car,
              [
                info("Make", vehicle["Make"]),
                info("Model", vehicle["Model"]),
                info("Year", vehicle["Model Year"]),
                info("VIN", data["vin"]),
              ],
            ),

            sectionCard(
              "Recall Information",
              Icons.warning_amber_rounded,
              [
                info("Total Recalls", recall["total_recalls"]),
                info("Open Recalls", recall["open_recalls"]),
              ],
            ),

            sectionCard(
              "Lease Terms",
              Icons.description_outlined,
              [
                info("Lease Term", sla["lease_term_months"]),
                info("Monthly Payment", sla["monthly_payment"]),
                info("Interest Rate", sla["interest_rate"]),
                info("Down Payment", sla["down_payment"]),
                info("Mileage Limit", sla["mileage_limit"]),
                info("Late Fees", sla["late_fees"]),
              ],
            ),

            sectionCard(
              "Safety Rating",
              Icons.health_and_safety_outlined,
              [
                info("Overall", safety["overall_rating"]),
                info("Front Crash", safety["front_crash"]),
                info("Side Crash", safety["side_crash"]),
                info("Rollover", safety["rollover"]),
              ],
            ),

            sectionCard(
              "Risk Assessment",
              Icons.speed_outlined,
              [
                // FIXED: Now passing both level and the 0-10 score
                riskGauge(risk["risk_level"] ?? "LOW", risk["risk_score"] ?? 0),
                info("Confidence", risk["confidence"]),
                SizedBox(height: 16),
                Text("Key Reasons", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                SizedBox(height: 8),
                bulletList(risk["reasons"] ?? [])
              ],
            ),

            sectionCard(
              "Fairness Score",
              Icons.balance_outlined,
              [
                fairnessGauge((fairness["fairness_score"] ?? 0).toDouble()),
                info("Category", fairness["fairness_category"]),
                SizedBox(height: 16),
                Text("Fairness Breakdown", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                SizedBox(height: 8),
                bulletList(fairness["fairness_reasons"] ?? [])
              ],
            ),

            sectionCard(
              "AI Advice",
              Icons.psychology_outlined,
              [
                bulletList(advice)
              ],
            ),

            sectionCard(
              "Contract Summary",
              Icons.summarize_outlined,
              [
                info("Overview", summary["overview"]),
                info("Financial Terms", summary["financial_terms"]),
                info("Vehicle Insights", summary["vehicle_insights"]),
                info("Risk Evaluation", summary["risk_evaluation"]),
                info("Recommendation", summary["recommendation"]),
              ],
            ),

            SizedBox(height: 10),

            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue[800],
                  foregroundColor: Colors.white,
                  padding: EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  elevation: 4,
                ),
                icon: Icon(Icons.chat_bubble_outline),
                label: Text("START NEGOTIATION", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                onPressed: (){
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => NegotiationScreen(
                        contractId: data["contract_id"].toString(),
                      ),
                    ),
                  );
                },
              ),
            ),

            SizedBox(height: 40),
          ],
        ),
      ),
    );
  }
}