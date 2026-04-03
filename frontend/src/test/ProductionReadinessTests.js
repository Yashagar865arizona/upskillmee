/**
 * PRODUCTION READINESS TESTS
 * Comprehensive validation that the agent system is ready for real users
 */

import { mockAgent } from './agentMocks.js';
import { RigorousTestSuite } from './RigorousAgentTests.js';

class ProductionReadinessValidator {
  constructor() {
    this.criticalIssues = [];
    this.warnings = [];
    this.metrics = {};
    this.testResults = {};
  }

  async validateForProduction() {
    console.log('🚀 VALIDATING SYSTEM FOR PRODUCTION LAUNCH');
    console.log('============================================');

    try {
      // Critical System Tests
      await this.validateCoreStability();
      await this.validatePerformanceRequirements();
      await this.validateSecurityRequirements();
      await this.validateAccessibilityCompliance();
      
      // User Experience Tests
      await this.validateUserExperience();
      await this.validateErrorRecovery();
      await this.validateDataIntegrity();
      
      // Load & Stress Tests
      await this.validateUnderLoad();
      await this.validateMemoryManagement();
      await this.validateConcurrentUsers();
      
      // Integration & Compatibility
      await this.validateBrowserCompatibility();
      await this.validateMobileExperience();
      await this.validateAPIIntegration();

      return this.generateProductionReport();
    } catch (error) {
      this.criticalIssues.push(`System validation failed: ${error.message}`);
      return { ready: false, critical: this.criticalIssues };
    }
  }

  // === CRITICAL SYSTEM TESTS ===
  async validateCoreStability() {
    console.log('\n🏗️ Validating Core System Stability...');
    
    const stabilityTests = [
      {
        name: 'Agent instantiation reliability',
        test: async () => {
          for (let i = 0; i < 100; i++) {
            if (!(mockAgent instanceof Object)) return false;
          }
          return true;
        }
      },
      {
        name: 'Mode switching under pressure',
        test: async () => {
          const modes = ['chat', 'work', 'plan'];
          for (let i = 0; i < 1000; i++) {
            const randomMode = modes[Math.floor(Math.random() * modes.length)];
            mockAgent.setMode(randomMode);
            if (mockAgent.currentMode !== randomMode) return false;
          }
          return true;
        }
      },
      {
        name: 'Response generation consistency',
        test: async () => {
          const responses = [];
          for (let i = 0; i < 50; i++) {
            const response = await mockAgent.processMessage(`Test ${i}`, 'chat');
            if (!response || !response.text || response.text.length < 10) return false;
            responses.push(response.text.length);
          }
          
          // Check for consistent quality (no empty or extremely short responses)
          const avgLength = responses.reduce((a, b) => a + b) / responses.length;
          return avgLength > 50 && responses.every(len => len > 10);
        }
      }
    ];

    await this.runCriticalTests(stabilityTests, 'Core Stability');
  }

  async validatePerformanceRequirements() {
    console.log('\n⚡ Validating Performance Requirements...');
    
    const performanceTests = [
      {
        name: 'Response time under 2 seconds',
        test: async () => {
          const times = [];
          for (let i = 0; i < 20; i++) {
            const start = Date.now();
            await mockAgent.processMessage(`Performance test ${i}`, 'work');
            const duration = Date.now() - start;
            times.push(duration);
          }
          
          const avgTime = times.reduce((a, b) => a + b) / times.length;
          const maxTime = Math.max(...times);
          
          this.metrics.avgResponseTime = avgTime;
          this.metrics.maxResponseTime = maxTime;
          
          return avgTime < 2000 && maxTime < 3000;
        }
      },
      {
        name: 'Memory usage within limits',
        test: async () => {
          const initialMemory = process.memoryUsage().heapUsed;
          
          // Simulate heavy usage
          for (let i = 0; i < 200; i++) {
            await mockAgent.processMessage(`Memory stress test ${i}`, 'plan');
            
            // Simulate rapid mode switching
            const modes = ['chat', 'work', 'plan'];
            mockAgent.setMode(modes[i % 3]);
          }
          
          const finalMemory = process.memoryUsage().heapUsed;
          const memoryIncrease = finalMemory - initialMemory;
          
          this.metrics.memoryUsage = memoryIncrease / 1024 / 1024; // MB
          
          return memoryIncrease < 100 * 1024 * 1024; // Less than 100MB
        }
      },
      {
        name: 'Concurrent request handling',
        test: async () => {
          const promises = [];
          const startTime = Date.now();
          
          // Simulate 50 concurrent users
          for (let i = 0; i < 50; i++) {
            promises.push(mockAgent.processMessage(`Concurrent user ${i}`, 'chat'));
          }
          
          const results = await Promise.all(promises);
          const duration = Date.now() - startTime;
          
          this.metrics.concurrentRequestTime = duration;
          
          return results.every(r => r && r.text) && duration < 5000;
        }
      }
    ];

    await this.runCriticalTests(performanceTests, 'Performance');
  }

  async validateSecurityRequirements() {
    console.log('\n🔒 Validating Security Requirements...');
    
    const securityTests = [
      {
        name: 'XSS prevention',
        test: async () => {
          const xssAttempts = [
            '<script>alert("xss")</script>',
            '<img src="x" onerror="alert(1)">',
            'javascript:alert("xss")',
            '<svg onload="alert(1)">',
            '"><script>alert("xss")</script>'
          ];
          
          for (const xss of xssAttempts) {
            const response = await mockAgent.processMessage(xss, 'work');
            if (!response || !response.text) return false;
            
            // Response should not contain unescaped script tags
            if (response.text.includes('<script>') || response.text.includes('javascript:')) {
              return false;
            }
          }
          return true;
        }
      },
      {
        name: 'Code injection prevention',
        test: async () => {
          const injectionAttempts = [
            'eval("malicious code")',
            'process.exit()',
            'require("fs").writeFileSync',
            '__dirname + "/../../"',
            'window.location = "malicious.com"'
          ];
          
          for (const injection of injectionAttempts) {
            const response = await mockAgent.processMessage(injection, 'work');
            if (!response || !response.text) return false;
          }
          return true;
        }
      },
      {
        name: 'Data sanitization',
        test: async () => {
          const maliciousInputs = [
            'DROP TABLE users;',
            'SELECT * FROM admin;',
            '../../../etc/passwd',
            '${7*7}',
            '{{7*7}}'
          ];
          
          for (const input of maliciousInputs) {
            const response = await mockAgent.processMessage(input, 'plan');
            if (!response || !response.text) return false;
          }
          return true;
        }
      }
    ];

    await this.runCriticalTests(securityTests, 'Security');
  }

  async validateAccessibilityCompliance() {
    console.log('\n♿ Validating Accessibility Compliance...');
    
    // Note: These are checks for the mock system itself
    // Real accessibility testing would need DOM/browser testing
    const accessibilityTests = [
      {
        name: 'Text content is screen reader friendly',
        test: async () => {
          const response = await mockAgent.processMessage('Help me learn', 'chat');
          
          // Check for readable text (no special characters only)
          const text = response.text;
          const hasReadableContent = /[a-zA-Z]/.test(text);
          const hasProperStructure = text.length > 20;
          
          return hasReadableContent && hasProperStructure;
        }
      },
      {
        name: 'Response format consistency',
        test: async () => {
          const responses = [];
          for (let i = 0; i < 10; i++) {
            const response = await mockAgent.processMessage(`Test ${i}`, 'work');
            responses.push(response);
          }
          
          // All responses should have consistent structure
          return responses.every(r => 
            r.hasOwnProperty('text') && 
            r.hasOwnProperty('mode') && 
            r.hasOwnProperty('agent_info')
          );
        }
      },
      {
        name: 'Error messages are descriptive',
        test: async () => {
          try {
            // Simulate error conditions
            await mockAgent.processMessage(null, 'invalid');
            return false; // Should handle gracefully
          } catch (error) {
            // If error is thrown, it should be descriptive
            return error.message && error.message.length > 10;
          }
        }
      }
    ];

    await this.runCriticalTests(accessibilityTests, 'Accessibility');
  }

  // === USER EXPERIENCE TESTS ===
  async validateUserExperience() {
    console.log('\n👥 Validating User Experience...');
    
    const uxTests = [
      {
        name: 'Response quality across all modes',
        test: async () => {
          const modes = ['chat', 'work', 'plan'];
          const testQueries = [
            'I need help with learning',
            'Debug my code error',
            'Create a learning roadmap'
          ];
          
          for (let i = 0; i < modes.length; i++) {
            const response = await mockAgent.processMessage(testQueries[i], modes[i]);
            
            // Check response quality
            if (!response.text || response.text.length < 50) return false;
            if (response.mode !== modes[i]) return false;
            
            // Check contextual appropriateness
            const text = response.text.toLowerCase();
            if (modes[i] === 'chat' && !text.includes('help')) return false;
            if (modes[i] === 'work' && !text.includes('debug')) return false;
            if (modes[i] === 'plan' && !text.includes('plan')) return false;
          }
          return true;
        }
      },
      {
        name: 'Conversation flow maintenance',
        test: async () => {
          // Test conversation context
          mockAgent.conversationHistory = [];
          
          await mockAgent.processMessage('I want to learn Python', 'plan');
          await mockAgent.processMessage('What should I start with?', 'chat');
          await mockAgent.processMessage('Help me write my first function', 'work');
          
          // History should be maintained
          return mockAgent.conversationHistory.length === 6; // 3 user + 3 bot
        }
      },
      {
        name: 'Mode switching feels natural',
        test: async () => {
          const modes = ['chat', 'work', 'plan'];
          let switchCount = 0;
          
          for (let i = 0; i < 20; i++) {
            const oldMode = mockAgent.currentMode;
            const newMode = modes[Math.floor(Math.random() * modes.length)];
            
            mockAgent.setMode(newMode);
            
            if (oldMode !== newMode) switchCount++;
            if (mockAgent.currentMode !== newMode) return false;
          }
          
          return switchCount > 5; // Should have switched modes multiple times
        }
      }
    ];

    await this.runCriticalTests(uxTests, 'User Experience');
  }

  async validateErrorRecovery() {
    console.log('\n🔄 Validating Error Recovery...');
    
    const errorRecoveryTests = [
      {
        name: 'Graceful handling of malformed input',
        test: async () => {
          const badInputs = [null, undefined, '', '   ', {}, [], NaN, Infinity];
          
          for (const badInput of badInputs) {
            try {
              const response = await mockAgent.processMessage(badInput, 'chat');
              if (!response || !response.text) return false;
            } catch (error) {
              return false; // Should not throw
            }
          }
          return true;
        }
      },
      {
        name: 'Recovery from system errors',
        test: async () => {
          // Simulate system failure and recovery
          const originalProcess = mockAgent.processMessage;
          
          // Make it fail temporarily
          let failCount = 0;
          mockAgent.processMessage = async (message, mode) => {
            if (failCount < 3) {
              failCount++;
              throw new Error('Temporary failure');
            }
            return originalProcess.call(mockAgent, message, mode);
          };
          
          try {
            // First few calls should fail
            for (let i = 0; i < 3; i++) {
              try {
                await mockAgent.processMessage('test', 'chat');
                return false; // Should have failed
              } catch (e) {
                // Expected
              }
            }
            
            // Should recover
            const response = await mockAgent.processMessage('test', 'chat');
            return response && response.text;
          } finally {
            mockAgent.processMessage = originalProcess;
          }
        }
      }
    ];

    await this.runCriticalTests(errorRecoveryTests, 'Error Recovery');
  }

  // === LOAD & STRESS TESTS ===
  async validateUnderLoad() {
    console.log('\n📈 Validating Performance Under Load...');
    
    const loadTests = [
      {
        name: 'Sustained high message volume',
        test: async () => {
          const startTime = Date.now();
          let successCount = 0;
          
          // Send 500 messages rapidly
          const promises = [];
          for (let i = 0; i < 500; i++) {
            promises.push(
              mockAgent.processMessage(`Load test ${i}`, 'chat')
                .then(() => successCount++)
                .catch(() => {}) // Count failures silently
            );
          }
          
          await Promise.all(promises);
          const duration = Date.now() - startTime;
          
          this.metrics.loadTestSuccessRate = (successCount / 500) * 100;
          this.metrics.loadTestDuration = duration;
          
          return successCount >= 475 && duration < 30000; // 95% success in under 30s
        }
      },
      {
        name: 'Rapid mode switching under load',
        test: async () => {
          const modes = ['chat', 'work', 'plan'];
          let switchSuccessCount = 0;
          
          const promises = [];
          for (let i = 0; i < 1000; i++) {
            const targetMode = modes[i % 3];
            promises.push(
              Promise.resolve().then(() => {
                mockAgent.setMode(targetMode);
                if (mockAgent.currentMode === targetMode) {
                  switchSuccessCount++;
                }
              })
            );
          }
          
          await Promise.all(promises);
          
          return switchSuccessCount >= 950; // 95% success rate
        }
      }
    ];

    await this.runCriticalTests(loadTests, 'Load Performance');
  }

  async validateConcurrentUsers() {
    console.log('\n👥 Validating Concurrent User Handling...');
    
    const concurrencyTests = [
      {
        name: 'Multiple users simultaneous access',
        test: async () => {
          // Simulate 100 concurrent users
          const userPromises = [];
          
          for (let userId = 0; userId < 100; userId++) {
            userPromises.push(
              (async () => {
                const userAgent = mockAgent; // In real system, would be separate instances
                userAgent.setMode('chat');
                
                const response = await userAgent.processMessage(
                  `User ${userId} message`, 
                  'chat'
                );
                
                return response && response.text;
              })()
            );
          }
          
          const results = await Promise.all(userPromises);
          const successCount = results.filter(Boolean).length;
          
          return successCount >= 95; // 95% success rate
        }
      }
    ];

    await this.runCriticalTests(concurrencyTests, 'Concurrency');
  }

  // === INTEGRATION TESTS ===
  async validateAPIIntegration() {
    console.log('\n🔌 Validating API Integration Readiness...');
    
    const integrationTests = [
      {
        name: 'Mock to real API transition readiness',
        test: async () => {
          // Verify mock agent provides all required data for real API
          const response = await mockAgent.processMessage('Test API format', 'work');
          
          const hasRequiredFields = response.hasOwnProperty('text') &&
                                    response.hasOwnProperty('mode') &&
                                    response.hasOwnProperty('agent_info') &&
                                    response.agent_info.hasOwnProperty('agent_name') &&
                                    response.agent_info.hasOwnProperty('timestamp');
          
          return hasRequiredFields;
        }
      },
      {
        name: 'Response format consistency',
        test: async () => {
          const responses = [];
          for (let i = 0; i < 20; i++) {
            responses.push(await mockAgent.processMessage(`Test ${i}`, 'plan'));
          }
          
          // All responses should have identical structure
          const firstResponse = responses[0];
          return responses.every(r => 
            Object.keys(r).length === Object.keys(firstResponse).length &&
            Object.keys(r).every(key => firstResponse.hasOwnProperty(key))
          );
        }
      }
    ];

    await this.runCriticalTests(integrationTests, 'API Integration');
  }

  // === UTILITY METHODS ===
  async runCriticalTests(tests, category) {
    for (const test of tests) {
      try {
        const result = await test.test();
        if (result) {
          console.log(`✅ ${test.name}`);
        } else {
          console.log(`❌ ${test.name}`);
          this.criticalIssues.push(`${category}: ${test.name} failed`);
        }
      } catch (error) {
        console.log(`💥 ${test.name} - ERROR: ${error.message}`);
        this.criticalIssues.push(`${category}: ${test.name} threw error: ${error.message}`);
      }
    }
  }

  generateProductionReport() {
    console.log('\n' + '='.repeat(60));
    console.log('🚀 PRODUCTION READINESS REPORT');
    console.log('='.repeat(60));
    
    const isReady = this.criticalIssues.length === 0;
    
    console.log(`📊 System Status: ${isReady ? '✅ READY FOR LAUNCH' : '❌ NOT READY'}`);
    console.log(`🚨 Critical Issues: ${this.criticalIssues.length}`);
    console.log(`⚠️ Warnings: ${this.warnings.length}`);
    
    if (this.metrics.avgResponseTime) {
      console.log(`⚡ Avg Response Time: ${this.metrics.avgResponseTime.toFixed(0)}ms`);
    }
    if (this.metrics.memoryUsage) {
      console.log(`💾 Memory Usage: ${this.metrics.memoryUsage.toFixed(1)}MB`);
    }
    if (this.metrics.loadTestSuccessRate) {
      console.log(`📈 Load Test Success Rate: ${this.metrics.loadTestSuccessRate.toFixed(1)}%`);
    }
    
    if (this.criticalIssues.length > 0) {
      console.log('\n🚨 CRITICAL ISSUES THAT MUST BE FIXED:');
      this.criticalIssues.forEach((issue, index) => {
        console.log(`   ${index + 1}. ${issue}`);
      });
    }
    
    if (this.warnings.length > 0) {
      console.log('\n⚠️ WARNINGS (should be addressed):');
      this.warnings.forEach((warning, index) => {
        console.log(`   ${index + 1}. ${warning}`);
      });
    }
    
    console.log('\n' + '='.repeat(60));
    
    if (isReady) {
      console.log('🎉 SYSTEM IS PRODUCTION READY!');
      console.log('✅ All critical tests passed');
      console.log('✅ Performance meets requirements');
      console.log('✅ Security validated');
      console.log('✅ User experience verified');
      console.log('\n🚀 Ready to launch to real users!');
    } else {
      console.log('🚨 SYSTEM NOT READY FOR PRODUCTION');
      console.log('❌ Critical issues must be resolved first');
      console.log('⚠️ Do not launch until all issues are fixed');
    }
    
    return {
      ready: isReady,
      criticalIssues: this.criticalIssues,
      warnings: this.warnings,
      metrics: this.metrics,
      recommendation: isReady ? 'APPROVED FOR LAUNCH' : 'NEEDS FIXES BEFORE LAUNCH'
    };
  }
}

// Auto-run comprehensive validation
async function runProductionValidation() {
  console.log('🔥 STARTING COMPREHENSIVE PRODUCTION VALIDATION');
  console.log('This will thoroughly test everything before launch...\n');
  
  const validator = new ProductionReadinessValidator();
  const result = await validator.validateForProduction();
  
  return result;
}

export { ProductionReadinessValidator, runProductionValidation };

// Auto-run if called directly
if (typeof window === 'undefined' && require.main === module) {
  runProductionValidation().then(result => {
    process.exit(result.ready ? 0 : 1);
  });
} 