import React, { useState } from 'react';
import {
  StyleSheet,
  Text,
  View,
  ScrollView,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  SafeAreaView,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';

interface LLMResponse {
  question: string;
  answer: string;
  context_found: boolean;
  sources_used: number;
  model_cached?: boolean;
}

const SAMPLE_QUESTIONS = [
  "What are the top NFL TE players?",
  "What is the NFL schedule for Week 13?",
  "Which NFL team has the best offense this season?",
  "Who are the top fantasy football quarterbacks?",
  "What are the current NFL standings?",
  "Which players are currently injured in the NFL?",
  "What is the difference between Standard, Half PPR, and Full PPR scoring?",
  "Who are the trending players in fantasy football?",
  "What NFL news should I know about this week?"
];

// Using local IP address for iOS Simulator compatibility
// If this doesn't work, try 'http://127.0.0.1:5001/query' or update with your current IP
const LLM_API_URL = 'http://192.168.1.162:5001/query';

export default function App() {
  const [selectedQuestion, setSelectedQuestion] = useState<string>('');
  const [customQuestion, setCustomQuestion] = useState<string>('');
  const [response, setResponse] = useState<LLMResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const queryLLM = async (question: string) => {
    if (!question.trim()) {
      setError('Please enter a question');
      return;
    }

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      // Using local IP address (192.168.1.162) for iOS Simulator compatibility
      const res = await fetch(LLM_API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: question.trim() }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || `HTTP error! status: ${res.status}`);
      }

      const data: LLMResponse = await res.json();
      setResponse(data);
    } catch (err: any) {
      setError(err.message || 'Failed to query LLM');
      console.error('Error querying LLM:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSampleQuestionPress = (question: string) => {
    setSelectedQuestion(question);
    setCustomQuestion('');
    queryLLM(question);
  };

  const handleCustomQuestionSubmit = () => {
    queryLLM(customQuestion);
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="dark" />
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <Text style={styles.title}>🏈 SportAI</Text>
          <Text style={styles.subtitle}>LLM Query Interface</Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Sample Questions</Text>
          {SAMPLE_QUESTIONS.map((question, index) => (
            <TouchableOpacity
              key={index}
              style={[
                styles.questionButton,
                selectedQuestion === question && styles.questionButtonActive
              ]}
              onPress={() => handleSampleQuestionPress(question)}
              disabled={loading}
            >
              <Text style={[
                styles.questionButtonText,
                selectedQuestion === question && styles.questionButtonTextActive
              ]}>
                {question}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Custom Question</Text>
          <TextInput
            style={styles.input}
            value={customQuestion}
            onChangeText={setCustomQuestion}
            placeholder="Enter your question here..."
            multiline
            editable={!loading}
          />
          <TouchableOpacity
            style={[styles.submitButton, (!customQuestion.trim() || loading) && styles.submitButtonDisabled]}
            onPress={handleCustomQuestionSubmit}
            disabled={loading || !customQuestion.trim()}
          >
            <Text style={styles.submitButtonText}>
              {loading ? 'Querying...' : 'Ask LLM'}
            </Text>
          </TouchableOpacity>
        </View>

        {loading && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#667eea" />
            <Text style={styles.loadingText}>
              Querying LLM... First query may take 30s-2min
            </Text>
          </View>
        )}

        {error && (
          <View style={styles.errorContainer}>
            <Text style={styles.errorTitle}>Error</Text>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        {response && !loading && (
          <View style={styles.responseContainer}>
            <Text style={styles.responseTitle}>Response</Text>
            
            <View style={styles.infoBox}>
              <Text style={styles.infoText}>
                <Text style={styles.infoLabel}>Question: </Text>
                {response.question}
              </Text>
              <Text style={styles.infoText}>
                <Text style={styles.infoLabel}>Context Found: </Text>
                {response.context_found ? 'Yes' : 'No'}
              </Text>
              <Text style={styles.infoText}>
                <Text style={styles.infoLabel}>Sources Used: </Text>
                {response.sources_used}
              </Text>
              {response.model_cached !== undefined && (
                <Text style={styles.infoText}>
                  <Text style={styles.infoLabel}>Model Cached: </Text>
                  {response.model_cached ? 'Yes' : 'No'}
                </Text>
              )}
            </View>

            <View style={styles.answerBox}>
              <Text style={styles.answerTitle}>Answer:</Text>
              <Text style={styles.answerText}>{response.answer}</Text>
            </View>

            <View style={styles.jsonBox}>
              <Text style={styles.jsonTitle}>Full JSON Response:</Text>
              <ScrollView style={styles.jsonScrollView}>
                <Text style={styles.jsonText}>
                  {JSON.stringify(response, null, 2)}
                </Text>
              </ScrollView>
            </View>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: 20,
  },
  header: {
    alignItems: 'center',
    marginBottom: 30,
    paddingTop: 20,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#667eea',
    marginBottom: 5,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    fontStyle: 'italic',
  },
  section: {
    marginBottom: 25,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  questionButton: {
    backgroundColor: '#fff',
    padding: 15,
    borderRadius: 10,
    marginBottom: 10,
    borderWidth: 2,
    borderColor: '#e0e0e0',
  },
  questionButtonActive: {
    backgroundColor: '#667eea',
    borderColor: '#667eea',
  },
  questionButtonText: {
    fontSize: 14,
    color: '#333',
  },
  questionButtonTextActive: {
    color: '#fff',
    fontWeight: '600',
  },
  input: {
    backgroundColor: '#fff',
    borderWidth: 2,
    borderColor: '#e0e0e0',
    borderRadius: 10,
    padding: 15,
    fontSize: 16,
    minHeight: 80,
    textAlignVertical: 'top',
    marginBottom: 15,
  },
  submitButton: {
    backgroundColor: '#667eea',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
  },
  submitButtonDisabled: {
    backgroundColor: '#ccc',
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  loadingContainer: {
    alignItems: 'center',
    padding: 30,
  },
  loadingText: {
    marginTop: 15,
    color: '#666',
    fontSize: 14,
  },
  errorContainer: {
    backgroundColor: '#fee',
    borderWidth: 2,
    borderColor: '#e74c3c',
    borderRadius: 10,
    padding: 15,
    marginBottom: 20,
  },
  errorTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#e74c3c',
    marginBottom: 10,
  },
  errorText: {
    color: '#c0392b',
    fontSize: 14,
  },
  responseContainer: {
    marginTop: 10,
  },
  responseTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#667eea',
    marginBottom: 15,
  },
  infoBox: {
    backgroundColor: '#f8f9fa',
    padding: 15,
    borderRadius: 10,
    marginBottom: 15,
  },
  infoText: {
    fontSize: 14,
    color: '#333',
    marginBottom: 8,
  },
  infoLabel: {
    fontWeight: 'bold',
    color: '#667eea',
  },
  answerBox: {
    backgroundColor: '#fff',
    padding: 15,
    borderRadius: 10,
    borderLeftWidth: 4,
    borderLeftColor: '#667eea',
    marginBottom: 15,
  },
  answerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#667eea',
    marginBottom: 10,
  },
  answerText: {
    fontSize: 16,
    color: '#333',
    lineHeight: 24,
  },
  jsonBox: {
    backgroundColor: '#282c34',
    borderRadius: 10,
    padding: 15,
    marginBottom: 20,
  },
  jsonTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#abb2bf',
    marginBottom: 10,
  },
  jsonScrollView: {
    maxHeight: 400,
  },
  jsonText: {
    fontSize: 12,
    color: '#abb2bf',
    fontFamily: 'monospace',
  },
});
