export const SAMPLE_PROGRAMS = [
  {
    id: 'clean',
    name: 'Clean Program',
    description: 'Valid C program with proper allocation and deallocation.',
    code: `// Test Case 1: Clean C Program
#include <stdio.h>
#include <stdlib.h>

int main() {
    int x = 10;
    int y = 20;
    int result = x + y;
    
    int *ptr = malloc(100);
    if (ptr != NULL) {
        *ptr = result;
        free(ptr);
    }
    return 0;
}`
  },
  {
    id: 'missing-semicolon',
    name: 'Missing Semicolon',
    description: 'Demonstrates syntax error detection on declaration.',
    code: `// Test Case 2: Missing Semicolon
#include <stdio.h>

int main() {
    int a = 5;
    int b = 10
    int sum = a + b;
    return 0;
}`
  },
  {
    id: 'memory-leak',
    name: 'Memory Leak',
    description: 'Allocates heap memory with malloc() but never frees it.',
    code: `// Test Case 3: Memory Leak Detection
#include <stdio.h>
#include <stdlib.h>

int main() {
    int *buffer = malloc(256);
    int count = 10;
    
    // Memory is never freed before returning!
    return 0;
}`
  },
  {
    id: 'double-free',
    name: 'Double Free',
    description: 'Attempts to free the same pointer twice.',
    code: `// Test Case 4: Double Free Detection
#include <stdio.h>
#include <stdlib.h>

int main() {
    int *data = malloc(50);
    free(data);
    
    // Critical error: freeing already freed pointer
    free(data);
    return 0;
}`
  },
  {
    id: 'duplicate-code',
    name: 'Duplicate Code',
    description: 'Contains structurally identical blocks suitable for refactoring.',
    code: `// Test Case 5: Code Duplication Detection
#include <stdio.h>

int main() {
    int val_a = 15;
    int val_b = 25;
    int sum1 = val_a + val_b;
    
    int item_x = 40;
    int item_y = 60;
    int sum2 = item_x + item_y;
    
    return 0;
}`
  },
  {
    id: 'undeclared-var',
    name: 'Undeclared Variable',
    description: 'Uses variable x without prior declaration.',
    code: `// Test Case 6: Undeclared Variable Detection
#include <stdio.h>

int main() {
    target_value = 100;
    return 0;
}`
  }
];
