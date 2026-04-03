// Simple test to verify mock agent system
import { mockAgent, MockAgentSimulator } from './agentMocks.js';

console.log('🧪 Testing Mock Agent System...');

// Test 1: Basic instantiation
console.log('✅ Test 1: Mock agent instantiated:', mockAgent instanceof MockAgentSimulator);

// Test 2: Mode switching
mockAgent.setMode('work');
console.log('✅ Test 2: Mode switched to work:', mockAgent.currentMode === 'work');

// Test 3: Message processing
async function testMessageProcessing() {
  try {
    const response = await mockAgent.processMessage('Help me debug my code', 'work');
    console.log('✅ Test 3: Message processed successfully');
    console.log('Response:', response.text.substring(0, 100) + '...');
    console.log('Mode:', response.mode);
    console.log('Agent name:', response.agent_info.agent_name);
    return true;
  } catch (error) {
    console.error('❌ Test 3 failed:', error);
    return false;
  }
}

// Test 4: Test scenarios
const scenarios = mockAgent.getTestScenarios();
console.log('✅ Test 4: Test scenarios loaded:', Object.keys(scenarios));

// Test 5: Learning plan generation
const plan = mockAgent.generateMockLearningPlan('full stack development');
console.log('✅ Test 5: Learning plan generated:', plan.title);

// Run async test
testMessageProcessing().then(success => {
  if (success) {
    console.log('🎉 All mock agent tests passed!');
  } else {
    console.log('❌ Some tests failed');
  }
});

export { mockAgent }; 