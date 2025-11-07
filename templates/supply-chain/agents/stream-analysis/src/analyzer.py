"""
AI-Powered Stream Analyzer
Uses Claude to analyze data quality in real-time
"""

import os
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None


class StreamAnalyzer:
    """
    Analyzes data streams using AI
    Detects quality issues, anomalies, and provides recommendations
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize analyzer
        
        Args:
            api_key: Anthropic API key (or from environment)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        
        if not self.api_key:
            print("⚠️  Warning: ANTHROPIC_API_KEY not set. AI analysis will be simulated.")
            self.client = None
        elif Anthropic is None:
            print("⚠️  Warning: anthropic package not installed. AI analysis will be simulated.")
            self.client = None
        else:
            self.client = Anthropic(api_key=self.api_key)

        # Rate Limiting
        self.last_call_time = 0
        self.min_call_interval = 5  # seconds between calls
    
    def analyze_batch(
        self,
        messages: List[Dict[str, Any]],
        topic: str
    ) -> Dict[str, Any]:
        """
        Analyze a batch of messages for quality issues
        
        Args:
            messages: List of messages from Kafka
            topic: Source topic name
            
        Returns:
            Analysis results with alerts
        """
        if len(messages) == 0:
            return {"alerts": [], "summary": "No messages to analyze"}
        
        # Use AI if available, otherwise use rule-based
        if self.client:
            # Check rate limit
            time_since_last = time.time() - self.last_call_time
            if time_since_last < self.min_call_interval:
                print(f"⏸️  Rate limited - using rule-based analysis (last call {time_since_last:.1f}s ago)")
                return self._rule_based_analysis(messages, topic)
            
            # Update timestamp and make AI call
            self.last_call_time = time.time()
            return self._ai_analysis(messages, topic)
        else:
            return self._rule_based_analysis(messages, topic)
    
    def _ai_analysis(
        self,
        messages: List[Dict[str, Any]],
        topic: str
    ) -> Dict[str, Any]:
        """AI-powered analysis using Claude"""
        
        # Prepare message sample (limit size)
        message_sample = messages[:10]  # Analyze first 10
        
        # Create prompt
        prompt = f"""You are a data quality analyst for an intelligent data platform. Analyze these messages from the '{topic}' topic:

Messages:
{json.dumps(message_sample, indent=2, default=str)}

Batch Stats:
- Total messages: {len(messages)}
- Topic: {topic}

Please analyze:
1. Data quality issues (missing fields, invalid values, inconsistencies)
2. Anomalies or unusual patterns
3. Schema violations
4. Potential data integrity problems

Provide your analysis in JSON format:
{{
  "severity": "LOW|MEDIUM|HIGH|CRITICAL",
  "issues_found": ["list of specific issues"],
  "anomalies": ["list of anomalies detected"],
  "recommendations": ["list of actionable recommendations"],
  "quality_score": <0-100>,
  "summary": "brief summary"
}}"""
        
        try:
            # Call Claude
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Parse response
            analysis_text = response.content[0].text
            
            # Extract JSON from response
            if "```json" in analysis_text:
                json_start = analysis_text.find("```json") + 7
                json_end = analysis_text.find("```", json_start)
                analysis_text = analysis_text[json_start:json_end].strip()
            
            analysis = json.loads(analysis_text)
            
            # Add metadata
            analysis["analyzed_messages"] = len(messages)
            analysis["topic"] = topic
            analysis["analysis_method"] = "AI"
            analysis["timestamp"] = datetime.utcnow().isoformat()
            
            return analysis
            
        except Exception as e:
            print(f"⚠️  AI analysis failed: {e}")
            # Fallback to rule-based
            return self._rule_based_analysis(messages, topic)
    
    def _rule_based_analysis(
        self,
        messages: List[Dict[str, Any]],
        topic: str
    ) -> Dict[str, Any]:
        """Rule-based analysis (fallback when AI unavailable)"""
        
        issues = []
        anomalies = []
        quality_score = 100.0
        
        # Check for missing fields
        if messages:
            first_msg = messages[0]
            required_fields = set(first_msg.keys())
            
            for i, msg in enumerate(messages):
                msg_fields = set(msg.keys())
                missing = required_fields - msg_fields
                if missing:
                    issues.append(f"Message {i}: Missing fields {missing}")
                    quality_score -= 5
        
        # Check for null values
        null_count = sum(
            1 for msg in messages 
            for value in msg.values() 
            if value is None
        )
        if null_count > len(messages) * 0.1:  # More than 10% nulls
            issues.append(f"High null value rate: {null_count} nulls in {len(messages)} messages")
            quality_score -= 10
        
        # Check message rate
        if len(messages) < 5:
            anomalies.append("Low message volume - possible upstream issue")
            quality_score -= 5
        
        # Determine severity
        if quality_score >= 90:
            severity = "LOW"
        elif quality_score >= 75:
            severity = "MEDIUM"
        elif quality_score >= 50:
            severity = "HIGH"
        else:
            severity = "CRITICAL"
        
        return {
            "severity": severity,
            "issues_found": issues or ["No issues detected"],
            "anomalies": anomalies or ["No anomalies detected"],
            "recommendations": [
                "Continue monitoring",
                "Validate upstream data sources",
                "Review schema definitions"
            ],
            "quality_score": max(0, quality_score),
            "summary": f"Analyzed {len(messages)} messages from {topic}. Quality score: {quality_score:.1f}",
            "analyzed_messages": len(messages),
            "topic": topic,
            "analysis_method": "RULE_BASED",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def should_alert(self, analysis: Dict[str, Any]) -> bool:
        """
        Determine if analysis results warrant an alert
        
        Args:
            analysis: Analysis results
            
        Returns:
            True if alert should be sent
        """
        severity = analysis.get("severity", "LOW")
        quality_score = analysis.get("quality_score", 100)
        
        # Alert on MEDIUM+ severity or quality score below 80
        return severity in ["MEDIUM", "HIGH", "CRITICAL"] or quality_score < 80
