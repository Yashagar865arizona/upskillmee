# **instructions.md**

## **General Guidelines**
1. **Analyze Before Acting**:  
   - Always review the existing codebase, structure, and dependencies before making changes or adding new code.  
   - Identify areas that need modification or expansion rather than guessing.  

2. **Consistency Is Key**:  
   - Avoid creating duplicate or redundant classes, functions, or modules.  
   - Follow the naming conventions and patterns already established in the project.  

3. **Follow Instructions Exactly**:  
   - Implement only what is specifically requested. Do not add unnecessary logic, classes, or functions.  
   - Clarify ambiguities before proceeding (e.g., "Should I extend the existing class or create a new one?").  

4. **Write Modular Code**:  
   - Avoid hardcoding values or creating large monolithic functions. Use constants, configuration files, or parameters for flexibility.  
   - Separate logic into small, reusable methods or functions wherever possible.  

---

## **Code Writing Guidelines**
1. **Class Management**:  
   - Use a **single class** for a specific purpose (e.g., one `Ball` class for all ball-related functionality).  
   - If a subclass is necessary, justify its creation with unique responsibilities that don't overlap with the parent class.  

2. **Avoid Overwriting or Removing**:  
   - Do not modify or delete existing functionality without explicit instructions.  
   - Make changes additive unless told otherwise.  

3. **Error-Free Outputs**:  
   - Run basic checks or validate syntax to avoid common mistakes (e.g., typos, missing imports, or unhandled exceptions).  

4. **Comments and Documentation**:  
   - Document all functions and classes with comments explaining their purpose, parameters, and expected outputs.  
   - Use docstrings where applicable.  

---

## **Debugging and Editing Guidelines**
1. **Edit Thoughtfully**:  
   - Before editing any code, identify **what the code does** and why the edit is necessary.  
   - Avoid unnecessary or speculative changes that can introduce bugs.  

2. **Fix One Problem at a Time**:  
   - Address issues sequentially, providing clear reasoning for changes made.  
   - Avoid introducing new logic while fixing bugs unless directly related.  

3. **No Guessing**:  
   - If uncertain, ask for clarification or describe the limitations in understanding the instructions.  
   - Do not proceed with assumptions about features or structure.  

---

## **Terminal Commands Guidelines**
1. **Do Not Run Commands Directly**:  
   - **Only** tell me what commands to run on my terminal, **do not execute them yourself**.
   - Ensure the terminal commands are clearly explained with instructions on what each does and how it fits into the task.

2. **Explain Commands**:  
   - Include a brief explanation of what the commands do and why they are necessary.

3. **Avoid Assumptions**:  
   - Assume the user’s terminal environment is different from yours. Always describe actions clearly.

4. **Provide Precise Commands**:  
   - Specify exactly what needs to be typed, and avoid unclear instructions. If multiple commands are required, ensure they are presented in sequence.

---

## **Testing and Validation**
1. **Always Test**:  
   - Validate new code with a test case or logging mechanism to ensure correctness.  
   - If tests exist, run them to ensure changes do not introduce regressions.  

2. **Review for Side Effects**:  
   - Check if changes impact unrelated parts of the codebase and mitigate unintended consequences.  
   - If you are unsure about how your changes might affect other parts of the code, run tests to confirm everything still works as expected.

---

## **Coding Example**

### **Do This:**
```typescript
// Ball.ts

// Represents a ball in a game, with consistent modular features
export class Ball {
  constructor(public radius: number, public color: string) {}

  // Calculate the ball's volume
  getVolume(): number {
    return (4 / 3) * Math.PI * Math.pow(this.radius, 3);
  }
}

### **Avoid This:**
// Hardcoded Ball Implementation (Bad Practice)
class Ball {
  radius = 5; // Hardcoded value
  color = "red"; // Hardcoded value

  getVolume() {
    return (4 / 3) * 3.14 * this.radius ** 3; // Inconsistent logic
  }
}