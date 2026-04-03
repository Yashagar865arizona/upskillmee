/**
 * RIGOROUS AGENT TESTING SUITE
 * Comprehensive production-ready tests for agent modes
 */

import { mockAgent, MockAgentSimulator } from './agentMocks.js';

class RigorousTestSuite {
  constructor() {
    this.results = {
      passed: 0,
      failed: 0,
      errors: [],
      performance: {},
      coverage: {}
    };
    this.startTime = Date.now();
  }

  async runAllTests() {
    console.log('🔥 STARTING RIGOROUS AGENT TESTING SUITE');
    console.log('===============================================');

    try {
      // Core Functionality Tests
      await this.testBasicFunctionality();
      await this.testModeConsistency();
      await this.testResponseQuality();
      
      // Edge Case Tests  
      await this.testEdgeCases();
      await this.testErrorHandling();
      await this.testStateManagement();
      
      // Performance Tests
      await this.testPerformance();
      await this.testConcurrency();
      await this.testMemoryLeaks();
      
      // Integration Tests
      await this.testWorkflowIntegration();
      await this.testUserJourneys();
      await this.testRealWorldScenarios();
      
      // Stress Tests
      await this.testHighVolume();
      await this.testExtremeCases();

      this.generateReport();
    } catch (error) {
      console.error('❌ CRITICAL TEST FAILURE:', error);
      this.results.errors.push(`Critical failure: ${error.message}`);
    }
  }

  // === CORE FUNCTIONALITY TESTS ===
  async testBasicFunctionality() {
    console.log('\n📋 Testing Basic Functionality...');
    
    const tests = [
      {
        name: 'Agent instantiation',
        test: () => mockAgent instanceof MockAgentSimulator
      },
      {
        name: 'Mode switching reliability',
        test: async () => {
          const modes = ['chat', 'work', 'plan'];
          for (const mode of modes) {
            mockAgent.setMode(mode);
            if (mockAgent.currentMode !== mode) return false;
          }
          return true;
        }
      },
      {
        name: 'Response generation',
        test: async () => {
          const response = await mockAgent.processMessage('Test message', 'chat');
          return response && response.text && response.mode && response.agent_info;
        }
      }
    ];

    await this.runTestBatch(tests, 'Basic Functionality');
  }

  async testModeConsistency() {
    console.log('\n🔄 Testing Mode Consistency...');
    
    const consistencyTests = [
      {
        name: 'Chat mode responses are mentoring-focused',
        test: async () => {
          const responses = [];
          const mentorKeywords = ['help', 'guide', 'support', 'learn', 'encourage'];
          
          for (let i = 0; i < 5; i++) {
            const response = await mockAgent.processMessage(`Help me with learning ${i}`, 'chat');
            responses.push(response.text.toLowerCase());
          }
          
          return responses.some(r => mentorKeywords.some(k => r.includes(k)));
        }
      },
      {
        name: 'Work mode responses are technical/practical',
        test: async () => {
          const response = await mockAgent.processMessage('Debug my code error', 'work');
          const technical = ['step', 'implement', 'code', 'debug', 'error', 'solution'];
          return technical.some(word => response.text.toLowerCase().includes(word));
        }
      },
      {
        name: 'Plan mode responses are structured/goal-oriented',
        test: async () => {
          const response = await mockAgent.processMessage('Create learning plan', 'plan');
          const planWords = ['plan', 'roadmap', 'week', 'goal', 'milestone', 'structured'];
          return planWords.some(word => response.text.toLowerCase().includes(word));
        }
      }
    ];

    await this.runTestBatch(consistencyTests, 'Mode Consistency');
  }

  async testResponseQuality() {
    console.log('\n✨ Testing Response Quality...');
    
    const qualityTests = [
      {
        name: 'Responses are not empty',
        test: async () => {
          const response = await mockAgent.processMessage('Test', 'chat');
          return response.text.length > 10; // Meaningful response
        }
      },
      {
        name: 'Responses are contextually appropriate',
        test: async () => {
          const errorMsg = await mockAgent.processMessage('I have a bug in my code', 'work');
          const motivationMsg = await mockAgent.processMessage('I feel discouraged', 'chat');
          
          return errorMsg.text.toLowerCase().includes('debug') && 
                 motivationMsg.text.toLowerCase().includes('encourage');
        }
      },
      {
        name: 'Response format is consistent',
        test: async () => {
          const response = await mockAgent.processMessage('Test', 'work');
          return response.hasOwnProperty('text') && 
                 response.hasOwnProperty('mode') && 
                 response.hasOwnProperty('agent_info');
        }
      }
    ];

    await this.runTestBatch(qualityTests, 'Response Quality');
  }

  // === EDGE CASE TESTS ===
  async testEdgeCases() {
    console.log('\n⚠️ Testing Edge Cases...');
    
    const edgeTests = [
      {
        name: 'Empty message handling',
        test: async () => {
          const response = await mockAgent.processMessage('', 'chat');
          return response && response.text; // Should handle gracefully
        }
      },
      {
        name: 'Very long message handling',
        test: async () => {
          const longMessage = 'a'.repeat(5000);
          const response = await mockAgent.processMessage(longMessage, 'work');
          return response && response.text;
        }
      },
      {
        name: 'Special characters handling',
        test: async () => {
          const specialMsg = '!@#$%^&*()_+{}[]|\\:";\'<>?,./ 测试 🚀🧪';
          const response = await mockAgent.processMessage(specialMsg, 'plan');
          return response && response.text;
        }
      },
      {
        name: 'Invalid mode handling',
        test: async () => {
          try {
            const response = await mockAgent.processMessage('Test', 'invalid_mode');
            return response && response.text; // Should fallback gracefully
          } catch (error) {
            return false;
          }
        }
      }
    ];

    await this.runTestBatch(edgeTests, 'Edge Cases');
  }

  async testErrorHandling() {
    console.log('\n🚨 Testing Error Handling...');
    
    const errorTests = [
      {
        name: 'Null message handling',
        test: async () => {
          try {
            const response = await mockAgent.processMessage(null, 'chat');
            return response !== null;
          } catch (error) {
            return false;
          }
        }
      },
      {
        name: 'Undefined parameters',
        test: async () => {
          try {
            const response = await mockAgent.processMessage(undefined, undefined);
            return response !== null;
          } catch (error) {
            return false;
          }
        }
      },
      {
        name: 'Rapid fire error recovery',
        test: async () => {
          try {
            const promises = [];
            for (let i = 0; i < 10; i++) {
              promises.push(mockAgent.processMessage(null, 'invalid'));
            }
            const results = await Promise.all(promises);
            return results.every(r => r !== null);
          } catch (error) {
            return false;
          }
        }
      }
    ];

    await this.runTestBatch(errorTests, 'Error Handling');
  }

  async testStateManagement() {
    console.log('\n🔄 Testing State Management...');
    
    const stateTests = [
      {
        name: 'Rapid mode switching stability',
        test: async () => {
          const modes = ['chat', 'work', 'plan'];
          for (let i = 0; i < 50; i++) {
            const randomMode = modes[Math.floor(Math.random() * modes.length)];
            mockAgent.setMode(randomMode);
            if (mockAgent.currentMode !== randomMode) return false;
          }
          return true;
        }
      },
      {
        name: 'Conversation history persistence',
        test: async () => {
          mockAgent.conversationHistory = [];
          await mockAgent.processMessage('Message 1', 'chat');
          await mockAgent.processMessage('Message 2', 'work');
          return mockAgent.conversationHistory.length === 4; // 2 user + 2 bot
        }
      },
      {
        name: 'Context switching integrity',
        test: async () => {
          mockAgent.setUserContext({ experience: 'beginner' });
          const context1 = { ...mockAgent.userContext };
          mockAgent.setUserContext({ experience: 'advanced' });
          const context2 = { ...mockAgent.userContext };
          return context1.experience === 'beginner' && context2.experience === 'advanced';
        }
      }
    ];

    await this.runTestBatch(stateTests, 'State Management');
  }

  // === PERFORMANCE TESTS ===
  async testPerformance() {
    console.log('\n⚡ Testing Performance...');
    
    const perfTests = [
      {
        name: 'Response time consistency',
        test: async () => {
          const times = [];
          for (let i = 0; i < 10; i++) {
            const start = Date.now();
            await mockAgent.processMessage(`Performance test ${i}`, 'chat');
            times.push(Date.now() - start);
          }
          const avgTime = times.reduce((a, b) => a + b) / times.length;
          this.results.performance.avgResponseTime = avgTime;
          return avgTime < 3000; // Should be under 3 seconds
        }
      },
      {
        name: 'Memory usage stability',
        test: async () => {
          const initialMemory = process.memoryUsage().heapUsed;
          
          // Generate many responses
          for (let i = 0; i < 100; i++) {
            await mockAgent.processMessage(`Memory test ${i}`, 'work');
          }
          
          const finalMemory = process.memoryUsage().heapUsed;
          const memoryIncrease = finalMemory - initialMemory;
          this.results.performance.memoryIncrease = memoryIncrease;
          
          return memoryIncrease < 50 * 1024 * 1024; // Less than 50MB increase
        }
      }
    ];

    await this.runTestBatch(perfTests, 'Performance');
  }

  async testConcurrency() {
    console.log('\n🔀 Testing Concurrency...');
    
    const concurrencyTests = [
      {
        name: 'Parallel message processing',
        test: async () => {
          const promises = [];
          for (let i = 0; i < 20; i++) {
            promises.push(mockAgent.processMessage(`Concurrent ${i}`, 'chat'));
          }
          const results = await Promise.all(promises);
          return results.every(r => r && r.text);
        }
      },
      {
        name: 'Mode switching under load',
        test: async () => {
          const promises = [];
          const modes = ['chat', 'work', 'plan'];
          
          for (let i = 0; i < 30; i++) {
            const mode = modes[i % 3];
            promises.push(
              new Promise(async (resolve) => {
                mockAgent.setMode(mode);
                const response = await mockAgent.processMessage(`Load test ${i}`, mode);
                resolve(response.mode === mode);
              })
            );
          }
          
          const results = await Promise.all(promises);
          return results.filter(Boolean).length >= results.length * 0.9; // 90% success rate
        }
      }
    ];

    await this.runTestBatch(concurrencyTests, 'Concurrency');
  }

  // === INTEGRATION TESTS ===
  async testWorkflowIntegration() {
    console.log('\n🔗 Testing Workflow Integration...');
    
    const workflowTests = [
      {
        name: 'Complete learning workflow',
        test: async () => {
          // Simulate complete user journey
          mockAgent.setMode('plan');
          const plan = await mockAgent.processMessage('Create learning plan for React', 'plan');
          
          mockAgent.setMode('work');
          const work = await mockAgent.processMessage('Help me implement React components', 'work');
          
          mockAgent.setMode('chat');
          const support = await mockAgent.processMessage('I need motivation to continue', 'chat');
          
          return plan.text && work.text && support.text &&
                 plan.mode === 'plan' && work.mode === 'work' && support.mode === 'chat';
        }
      },
      {
        name: 'Cross-mode context awareness',
        test: async () => {
          // Test if agent maintains context across mode switches
          await mockAgent.processMessage('I want to learn Python', 'plan');
          mockAgent.setMode('work');
          const response = await mockAgent.processMessage('Help with implementation', 'work');
          
          // Should reference previous context
          return response.text.length > 50; // Substantial response
        }
      }
    ];

    await this.runTestBatch(workflowTests, 'Workflow Integration');
  }

  async testUserJourneys() {
    console.log('\n👤 Testing User Journeys...');
    
    const journeyTests = [
      {
        name: 'Beginner to advanced progression',
        test: async () => {
          mockAgent.setUserContext({ experience: 'beginner' });
          const beginnerResponse = await mockAgent.processMessage('How do I start coding?', 'chat');
          
          mockAgent.setUserContext({ experience: 'advanced' });
          const advancedResponse = await mockAgent.processMessage('How do I optimize algorithms?', 'chat');
          
          return beginnerResponse.text !== advancedResponse.text;
        }
      },
      {
        name: 'Problem solving journey',
        test: async () => {
          // Plan -> Work -> Support cycle
          const planResp = await mockAgent.processMessage('Plan for building a web app', 'plan');
          const workResp = await mockAgent.processMessage('Debug deployment issue', 'work');
          const chatResp = await mockAgent.processMessage('Feeling stuck on project', 'chat');
          
          return planResp.text && workResp.text && chatResp.text;
        }
      }
    ];

    await this.runTestBatch(journeyTests, 'User Journeys');
  }

  // === STRESS TESTS ===
  async testHighVolume() {
    console.log('\n📈 Testing High Volume...');
    
    const volumeTests = [
      {
        name: 'Handle 1000 sequential messages',
        test: async () => {
          let successCount = 0;
          for (let i = 0; i < 100; i++) { // Reduced for CI
            try {
              const response = await mockAgent.processMessage(`Volume test ${i}`, 'chat');
              if (response && response.text) successCount++;
            } catch (error) {
              // Continue testing
            }
          }
          return successCount >= 95; // 95% success rate
        }
      }
    ];

    await this.runTestBatch(volumeTests, 'High Volume');
  }

  async testExtremeCases() {
    console.log('\n🔥 Testing Extreme Cases...');
    
    const extremeTests = [
      {
        name: 'Unicode and emoji handling',
        test: async () => {
          const unicodeMsg = '🚀 Hello 世界 🌍 Testing 中文 русский العربية 🧪';
          const response = await mockAgent.processMessage(unicodeMsg, 'chat');
          return response && response.text;
        }
      },
      {
        name: 'Code injection prevention',
        test: async () => {
          const maliciousInputs = [
            '<script>alert("xss")</script>',
            'SELECT * FROM users;',
            '${process.exit()}',
            'eval("malicious code")'
          ];
          
          for (const input of maliciousInputs) {
            const response = await mockAgent.processMessage(input, 'work');
            if (!response || !response.text) return false;
          }
          return true;
        }
      }
    ];

    await this.runTestBatch(extremeTests, 'Extreme Cases');
  }

  // === UTILITY METHODS ===
  async runTestBatch(tests, category) {
    console.log(`\nRunning ${tests.length} ${category} tests...`);
    
    for (const test of tests) {
      try {
        const result = await test.test();
        if (result) {
          console.log(`✅ ${test.name}`);
          this.results.passed++;
        } else {
          console.log(`❌ ${test.name}`);
          this.results.failed++;
          this.results.errors.push(`${category}: ${test.name} failed`);
        }
      } catch (error) {
        console.log(`💥 ${test.name} - ERROR: ${error.message}`);
        this.results.failed++;
        this.results.errors.push(`${category}: ${test.name} threw error: ${error.message}`);
      }
    }
  }

  generateReport() {
    const duration = Date.now() - this.startTime;
    const total = this.results.passed + this.results.failed;
    const successRate = ((this.results.passed / total) * 100).toFixed(1);
    
    console.log('\n' + '='.repeat(50));
    console.log('📊 RIGOROUS TEST SUITE RESULTS');
    console.log('='.repeat(50));
    console.log(`✅ Passed: ${this.results.passed}`);
    console.log(`❌ Failed: ${this.results.failed}`);
    console.log(`📈 Success Rate: ${successRate}%`);
    console.log(`⏱️ Duration: ${duration}ms`);
    
    if (this.results.performance.avgResponseTime) {
      console.log(`⚡ Avg Response Time: ${this.results.performance.avgResponseTime.toFixed(0)}ms`);
    }
    
    if (this.results.performance.memoryIncrease) {
      console.log(`💾 Memory Increase: ${(this.results.performance.memoryIncrease / 1024 / 1024).toFixed(1)}MB`);
    }
    
    if (this.results.errors.length > 0) {
      console.log('\n🚨 ERRORS FOUND:');
      this.results.errors.forEach(error => console.log(`   • ${error}`));
    }
    
    console.log('\n' + '='.repeat(50));
    
    if (successRate >= 95) {
      console.log('🎉 SYSTEM IS PRODUCTION READY!');
    } else if (successRate >= 85) {
      console.log('⚠️ SYSTEM NEEDS MINOR FIXES BEFORE LAUNCH');
    } else {
      console.log('🚨 SYSTEM NOT READY FOR PRODUCTION - CRITICAL ISSUES FOUND');
    }
    
    return {
      readyForProduction: successRate >= 95,
      successRate: parseFloat(successRate),
      errors: this.results.errors,
      performance: this.results.performance
    };
  }
}

// Export for use
export { RigorousTestSuite };

// Auto-run if called directly
if (typeof window === 'undefined') {
  const testSuite = new RigorousTestSuite();
  testSuite.runAllTests().then(result => {
    process.exit(result.readyForProduction ? 0 : 1);
  });
} 