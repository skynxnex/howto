# Benchmark Results — 2026-03-25 12:28

## Prompt
```
Write a Kotlin function that:
1. Takes a list of integers
2. Returns a map where keys are "even" and "odd"
3. Each key maps to the sum of numbers in that category
4. Handle empty list gracefully

Include a brief docstring and one usage example in a comment.
```

## Speed Summary

| | Time to first token | Total time | Output tokens |
|---|---|---|---|
| Claude Sonnet 4.6 (Vertex AI) | 2443 ms | 14716 ms | ~951 |
| qwen3:14b (Ollama remote, think=off) | 304 ms | 15849 ms | ~188 |

---

## Claude Sonnet 4.6 (Vertex AI)

```kotlin
```kotlin
/**
 * Partitions a list of integers into even and odd categories,
 * returning the sum of each category.
 *
 * @param numbers The list of integers to process.
 * @return A map with keys "even" and "odd", each mapping to the
 *         sum of numbers in that category. Returns 0 for both
 *         keys if the list is empty.
 *
 * Usage example:
 *   val result = sumByParity(listOf(1, 2, 3, 4, 5))
 *   // result => {"even"=6, "odd"=9}
 */
fun sumByParity(numbers: List<Int>): Map<String, Int> {
    // Handle empty list gracefully by providing default value of 0
    if (numbers.isEmpty()) {
        return mapOf("even" to 0, "odd" to 0)
    }

    return numbers
        .groupBy { if (it % 2 == 0) "even" else "odd" }
        .mapValues { (_, nums) -> nums.sum() }
        .withDefault { 0 }  // Ensures both keys exist even if one category is absent
        .let { map ->
            mapOf(
                "even" to (map["even"] ?: 0),
                "odd" to (map["odd"] ?: 0)
            )
        }
}

fun main() {
    // Basic usage
    val mixed = sumByParity(listOf(1, 2, 3, 4, 5))
    println("Mixed list:  $mixed")  // {even=6, odd=9}

    // All even numbers
    val allEven = sumByParity(listOf(2, 4, 6, 8))
    println("All even:    $allEven")  // {even=20, odd=0}

    // All odd numbers
    val allOdd = sumByParity(listOf(1, 3, 5, 7))
    println("All odd:     $allOdd")  // {even=0, odd=16}

    // Empty list
    val empty = sumByParity(emptyList())
    println("Empty list:  $empty")  // {even=0, odd=0}

    // Negative numbers
    val withNegatives = sumByParity(listOf(-3, -2, -1, 0, 1, 2, 3))
    println("Negatives:   $withNegatives")  // {even=0, odd=0}

    // Single element
    val single = sumByParity(listOf(7))
    println("Single item: $single")  // {even=0, odd=7}
}
```

### Key Design Decisions

| Decision | Reason |
|---|---|
| Always return both keys | Avoids null checks for callers; consistent contract |
| Default value of `0` | Mathematically correct (sum of empty set = 0) |
| `groupBy` + `mapValues` | Idiomatic Kotlin, clean and readable |
| Early return for empty list | Explicit and clear intent |

### How It Works

```
Input: [1, 2, 3, 4, 5]
         │
         ▼
groupBy  → { "odd" = [1, 3, 5], "even" = [2, 4] }
         │
         ▼
mapValues→ { "odd" = 9,         "even" = 6      }
         │
         ▼
Output:  { "even" = 6, "odd" = 9 }
```

> **Note on negative numbers:** `%` in Kotlin can return negative remainders (e.g., `-3 % 2 == -1`), so the check `it % 2 == 0` still correctly identifies even numbers since only `0` signals evenness.
```

## qwen3:14b (Ollama remote, think=off)

```kotlin
```kotlin
/**
 * Groups integers in a list into even and odd categories and returns the sum for each.
 * Handles empty lists by returning zero sums for both categories.
 *
 * @param numbers A list of integers to be categorized and summed.
 * @return A map with keys "even" and "odd" mapping to their respective sums.
 */
fun sumEvenAndOdd(numbers: List<Int>): Map<String, Int> {
    val evenSum = numbers.filter { it % 2 == 0 }.sum()
    val oddSum = numbers.filter { it % 2 != 0 }.sum()
    return mapOf("even" to evenSum, "odd" to oddSum)
}

// Example usage:
// val result = sumEvenAndOdd(listOf(1, 2, 3, 4, 5))
// println(result) // Output: {even=6, odd=9}
```
```

