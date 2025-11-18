# Inline AI Quick Reference Guide

## Command Reference

### 1. Proofread Text

**Command:**
```json
{
  "command": "proofread_text",
  "text": "Your text with potential erors and mistakes.",
  "show_changes": true
}
```

**Use Cases:**
- Fix grammar errors
- Correct spelling mistakes
- Improve punctuation
- Enhance writing style

---

### 2. Rewrite Text

**Command:**
```json
{
  "command": "rewrite_text",
  "text": "Your original text here.",
  "tone": "professional"
}
```

**Available Tones:**
- `professional` - Formal, business-appropriate
- `friendly` - Warm, conversational
- `concise` - Brief, to-the-point

---

### 3. Summarize Text

**Command:**
```json
{
  "command": "summarize_text",
  "text": "Long text to summarize...",
  "max_sentences": 3
}
```

**Use Cases:**
- Create quick summaries
- Extract main points
- Condense long documents

---

### 4. Format as Key Points

**Command:**
```json
{
  "command": "format_text",
  "text": "Text containing multiple important points...",
  "format": "key_points",
  "num_points": 5
}
```

**Output:** Markdown bulleted list
**Use Cases:**
- Meeting notes
- Article highlights
- Executive summaries

---

### 5. Format as List

**Command:**
```json
{
  "command": "format_text",
  "text": "Items: first, second, third...",
  "format": "list"
}
```

**Output:** Numbered or bulleted list (auto-detected)
**Use Cases:**
- To-do lists
- Step-by-step instructions
- Shopping lists

---

### 6. Format as Table

**Command:**
```json
{
  "command": "format_text",
  "text": "Data with rows and columns...",
  "format": "table"
}
```

**Output:** Markdown table
**Use Cases:**
- Data comparison
- Report generation
- Structured information

---

### 7. Compose New Content

**Command:**
```json
{
  "command": "compose_text",
  "prompt": "Write a professional email requesting time off",
  "context": "I need time off next week for a family event",
  "max_length": 200
}
```

**Use Cases:**
- Email composition
- Message drafting
- Content generation
- Idea expansion

---

## Python API Reference

### Proofreader

```python
from voice_assistant.inline_ai import TextProofreader

# Initialize
proofreader = TextProofreader(llm_provider, config)

# Use
result = await proofreader.proofread(
    text="Text with errors",
    show_changes=True
)

# Check results
if result.success:
    print(f"Corrected: {result.proofread_text}")
    print(f"Changes: {result.num_changes}")
```

### Formatter

```python
from voice_assistant.inline_ai import TextFormatter, FormatType

# Initialize
formatter = TextFormatter(llm_provider, config)

# Summary
summary = await formatter.summary(text, max_sentences=3)

# Key Points
points = await formatter.key_points(text, num_points=5)

# List
list_result = await formatter.to_list(text)

# Table
table = await formatter.to_table(text)
```

### Composer

```python
from voice_assistant.inline_ai import ContentComposer

# Initialize
composer = ContentComposer(llm_provider, config)

# Basic composition
result = await composer.compose(
    prompt="Write about AI",
    context="Focus on practical applications"
)

# Email
email = await composer.compose_email(
    prompt="Request meeting",
    context="Discuss Q4 goals"
)

# Message
msg = await composer.compose_message(
    prompt="Say thanks for help"
)
```

---

## Configuration Options

### In `config.yaml`:

```yaml
inline_ai:
  # Proofreading
  proofread:
    enabled: true
    show_changes: true

  # Formatting
  formatting:
    enabled: true
    summary_length: 100
    key_points_count: 5

  # Composition
  compose:
    enabled: true
    max_length: 500
```

---

## Response Types

### Success Response

```json
{
  "type": "proofread_complete|format_complete|compose_complete",
  "original": "Original text",
  "result_field": "Processed text",
  "tokens_used": 50,
  "processing_time_ms": 1500,
  "metadata": {...}
}
```

### Error Response

```json
{
  "type": "inline_ai_error",
  "error": "Description of what went wrong"
}
```

---

## Common Patterns

### Sequential Processing

```python
# 1. Proofread
proofread_result = await proofreader.proofread(text)

# 2. Format
if proofread_result.success:
    format_result = await formatter.key_points(
        proofread_result.proofread_text
    )
```

### Concurrent Processing

```python
# Process multiple texts at once
results = await asyncio.gather(
    proofreader.proofread(text1),
    proofreader.proofread(text2),
    formatter.summary(text3)
)
```

### Error Handling

```python
try:
    result = await composer.compose(prompt)
    if not result.success:
        logger.error(f"Composition failed: {result.error}")
        # Handle error
except asyncio.TimeoutError:
    logger.error("Operation timed out")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

---

## Performance Tips

1. **Use appropriate timeouts:**
   ```python
   result = await proofreader.proofread(text, timeout_seconds=5.0)
   ```

2. **Batch similar operations:**
   ```python
   tasks = [formatter.summary(t) for t in texts]
   results = await asyncio.gather(*tasks)
   ```

3. **Use quick methods for simple cases:**
   ```python
   # Faster, no change tracking
   result = await proofreader.proofread_quick(text)
   ```

4. **Set appropriate lengths:**
   ```python
   # Shorter = faster
   result = await composer.compose(prompt, max_length=100)
   ```

---

## Testing

### Run Tests

```bash
# All inline AI tests
pytest tests/inline_ai/ -v

# Specific module
pytest tests/inline_ai/test_proofreader.py -v

# With coverage
pytest tests/inline_ai/ --cov=voice_assistant.inline_ai
```

### Example Test

```python
@pytest.mark.asyncio
async def test_proofreading():
    result = await proofreader.proofread("Text with eror")
    assert result.success
    assert "error" in result.proofread_text
```

---

## Troubleshooting

### Issue: Timeout errors

**Solution:** Increase timeout or reduce text length
```python
result = await proofreader.proofread(text, timeout_seconds=10.0)
```

### Issue: Empty results

**Solution:** Check text length validation
```python
if len(text) < 10:
    logger.warning("Text too short")
```

### Issue: LLM errors

**Solution:** Implement retry logic or fallback
```python
try:
    result = await proofreader.proofread(text)
except Exception as e:
    # Fallback or retry
    result = await proofreader.proofread(text[:1000])  # Shorter
```

---

## Best Practices

1. **Always check `result.success` before using output**
2. **Handle errors gracefully with user-friendly messages**
3. **Use appropriate format types for content**
4. **Provide context when composing for better results**
5. **Monitor `processing_time_ms` for performance**
6. **Log errors for debugging**
7. **Test with various text lengths and types**

---

## Resources

- **Full Documentation:** `INLINE_AI_IMPLEMENTATION_SUMMARY.md`
- **Config Example:** `config.yaml`
- **Test Examples:** `tests/inline_ai/`
- **Source Code:** `src/voice_assistant/inline_ai/`
