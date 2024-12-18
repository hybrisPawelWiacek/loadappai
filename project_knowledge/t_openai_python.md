To use the OpenAI API with the GPT-4o-mini model in Python, follow these steps:

## Installation and Setup

1. Install the OpenAI Python library:
```bash
pip install openai
```

2. Import the necessary modules and set up your API key:
```python
from openai import OpenAI

client = OpenAI(api_key="your_api_key_here")
```

Replace "your_api_key_here" with your actual OpenAI API key[3].

## Making API Calls

To generate text using the GPT-4o-mini model:

```python
completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Write a haiku about recursion in programming."}
    ]
)

print(completion.choices[0].message.content)
```

This code snippet sends a request to the GPT-4o-mini model, asking it to write a haiku about recursion in programming[1][4].

## Key Features of GPT-4o-mini

GPT-4o-mini is a multimodal model designed to handle a combination of text and image inputs, with text output capabilities[1]. It offers:

- Higher accuracy than GPT-3.5 Turbo
- Comparable speed to GPT-3.5 Turbo
- Support for multimodal inputs and outputs
- Lower cost compared to larger models

## Additional Considerations

- **Context Window**: GPT-4o-mini has a context window of 128,000 tokens, allowing for processing of longer inputs[6].
- **Output Tokens**: The model can generate up to 4,096 tokens in a single response[6].
- **Use Case**: GPT-4o-mini is suitable for smaller tasks, including vision tasks, and is recommended as a replacement for gpt-3.5-turbo in many scenarios[6].

## Streaming Responses

For longer responses, you can use streaming to get partial results as they're generated:

```python
stream = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Write a short story about AI"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")
```

This approach allows you to process and display the response in real-time as it's being generated[4].

By following these steps and guidelines, you can effectively use the OpenAI API with the GPT-4o-mini model in Python for various text generation tasks.

Citations:
[1] https://cookbook.openai.com/examples/gpt4o/introduction_to_gpt4o
[2] https://platform.openai.com/docs/quickstart
[3] https://www.datacamp.com/tutorial/gpt4o-api-openai-tutorial
[4] https://platform.openai.com/docs/api-reference/chat
[5] https://wandb.ai/onlineinference/gpt-python/reports/GPT-4o-Python-quickstart-using-the-OpenAI-API--VmlldzozODI1MjY4
[6] https://platform.openai.com/docs/models/gp
[7] https://platform.openai.com/docs/guides/gpt

Certainly! Here are more comprehensive examples of how to use the OpenAI API in Python for various applications:

## Text Generation

```python
from openai import OpenAI
import os

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def generate_text(prompt, max_tokens=100):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_tokens
    )
    return response.choices[0].message.content

# Example usage
prompt = "Explain the concept of quantum computing in simple terms."
generated_text = generate_text(prompt, max_tokens=150)
print(generated_text)
```

## Chatbot

```python
from openai import OpenAI
import os

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def chatbot():
    conversation_history = []
    print("Chatbot: Hello! How can I assist you today? (Type 'exit' to end the conversation)")

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break

        conversation_history.append({"role": "user", "content": user_input})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation_history
        )

        assistant_response = response.choices[0].message.content
        print("Chatbot:", assistant_response)

        conversation_history.append({"role": "assistant", "content": assistant_response})

chatbot()
```

## Image Generation

```python
from openai import OpenAI
import os
import requests

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def generate_image(prompt, size="1024x1024"):
    response = client.images.generate(
        prompt=prompt,
        n=1,
        size=size
    )
    image_url = response.data[0].url
    return image_url

def save_image(url, filename):
    response = requests.get(url)
    with open(filename, "wb") as f:
        f.write(response.content)

# Example usage
prompt = "A futuristic city with flying cars and holographic billboards"
image_url = generate_image(prompt)
save_image(image_url, "futuristic_city.png")
print(f"Image saved as futuristic_city.png")
```

## Text Embeddings

```python
from openai import OpenAI
import os
import numpy as np

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def get_embedding(text, model="text-embedding-3-large"):
    response = client.embeddings.create(
        input=text,
        model=model
    )
    return response.data[0].embedding

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# Example usage
text1 = "The quick brown fox jumps over the lazy dog"
text2 = "A fast auburn canine leaps above an idle hound"

embedding1 = get_embedding(text1)
embedding2 = get_embedding(text2)

similarity = cosine_similarity(embedding1, embedding2)
print(f"Cosine similarity between the two texts: {similarity}")
```

## Fine-tuning a Model

```python
from openai import OpenAI
import os

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def prepare_training_data(filename):
    with open(filename, 'rb') as file:
        return client.files.create(file=file, purpose='fine-tune')

def start_fine_tuning(file_id, model="gpt-3.5-turbo"):
    response = client.fine_tuning.jobs.create(
        training_file=file_id,
        model=model
    )
    return response.id

def check_fine_tuning_status(job_id):
    return client.fine_tuning.jobs.retrieve(job_id)

# Example usage
training_file = prepare_training_data("training_data.jsonl")
job_id = start_fine_tuning(training_file.id)
print(f"Fine-tuning job started with ID: {job_id}")

# Check status (you'd typically do this periodically)
status = check_fine_tuning_status(job_id)
print(f"Current status: {status.status}")
```

These examples demonstrate various ways to use the OpenAI API in Python applications, including text generation, chatbots, image generation, text embeddings, and fine-tuning models. Remember to handle exceptions, implement proper error checking, and adhere to OpenAI's usage guidelines and best practices when developing your applications[1][2][3][4][7].

Citations:
[1] https://www.geeksforgeeks.org/openai-python-api/
[2] https://tilburg.ai/2024/07/become-a-prompt-engineer-openai-api-python/
[3] https://www.sitepoint.com/python-build-ai-tools-openai-api/
[4] https://platform.openai.com/docs/quickstart
[5] https://pypi.org/project/openai/0.26.5/
[6] https://platform.openai.com/docs/api-reference/chat
[7] https://www.newhorizons.com/resources/blog/the-complete-guide-for-using-the-openai-python-api
[8] https://tilburg.ai/2024/03/openai-api-tutorial-python/

Integrating the OpenAI API into a web application involves several steps, from setting up the environment to handling responses effectively. Below is a detailed guide to help you integrate OpenAI's API into your web application:

## **1. Prerequisites**
Before starting, ensure you have:
- An OpenAI API key (sign up at OpenAI's website to obtain it).
- A development environment set up for your preferred language or framework (e.g., Python, JavaScript, etc.).
- Basic knowledge of HTTP requests and web development.

---

## **2. Setting Up the Environment**
### **For Python Applications**
1. Install the OpenAI library:
   ```bash
   pip install openai
   ```
2. Create a `.env` file to securely store your API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
3. Load the API key in your application using `dotenv`:
   ```python
   from dotenv import load_dotenv
   import os
   import openai

   load_dotenv()
   openai.api_key = os.getenv("OPENAI_API_KEY")
   ```

### **For JavaScript Applications**
1. Install Axios or use the Fetch API for HTTP requests.
2. Store the API key securely on the server side, not in client-side code, to prevent exposure.

---

## **3. Making API Requests**
### Example: Text Completion
```python
import openai

def get_response(prompt):
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=100,
        temperature=0.7
    )
    return response['choices'][0]['text']

print(get_response("Explain how AI can improve education."))
```

### Example: Using JavaScript with Axios
```javascript
const axios = require('axios');

const apiKey = process.env.OPENAI_API_KEY;

async function getResponse(prompt) {
    const response = await axios.post('https://api.openai.com/v1/completions', {
        model: "text-davinci-003",
        prompt: prompt,
        max_tokens: 100,
        temperature: 0.7,
    }, {
        headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json',
        }
    });
    console.log(response.data.choices[0].text);
}

getResponse("What are the benefits of AI in healthcare?");
```

---

## **4. Integrating with Web Applications**
### **React Application Example**
1. Install Axios:
   ```bash
   npm install axios
   ```
2. Create an API service file (`openaiService.js`):
   ```javascript
   import axios from "axios";

   const API_KEY = process.env.REACT_APP_OPENAI_API_KEY;

   export const fetchOpenAIResponse = async (prompt) => {
       const response = await axios.post('https://api.openai.com/v1/completions', {
           model: "text-davinci-003",
           prompt: prompt,
           max_tokens: 100,
           temperature: 0.7,
       }, {
           headers: {
               'Authorization': `Bearer ${API_KEY}`,
               'Content-Type': 'application/json',
           }
       });
       return response.data;
   };
   ```
3. Use the service in a React component:
   ```javascript
   import React, { useState } from "react";
   import { fetchOpenAIResponse } from "./openaiService";

   const App = () => {
       const [prompt, setPrompt] = useState("");
       const [response, setResponse] = useState("");

       const handleSubmit = async (e) => {
           e.preventDefault();
           const data = await fetchOpenAIResponse(prompt);
           setResponse(data.choices[0].text);
       };

       return (
           <div>
               <h1>OpenAI Integration</h1>
               <form onSubmit={handleSubmit}>
                   <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} />
                   <button type="submit">Get Response</button>
               </form>
               <p>{response}</p>
           </div>
       );
   };

   export default App;
   ```

---

## **5. Best Practices**
- **Secure API Keys**: Store keys in environment variables or server-side code to prevent exposure.
- **Optimize Requests**: Use caching mechanisms to reduce redundant requests and minimize costs.
- **Handle Errors Gracefully**: Implement error handling for scenarios like rate limits or invalid inputs.
- **Monitor Usage**: Track your API usage to avoid unexpected charges and ensure efficiency.
- **Respect Privacy**: Ensure compliance with data protection regulations when handling user data.

---

## **6. Advanced Features**
Once basic integration is complete, explore advanced capabilities:
- **Fine-tuning Models**: Train models on custom datasets for domain-specific tasks.
- **Batch Processing**: Handle multiple requests simultaneously using asynchronous programming.
- **Multimodal Inputs**: Use models like DALL·E for image generation or Whisper for audio transcription.

---

By following these steps and best practices, you can seamlessly integrate OpenAI's API into your web application to enhance functionality and user experience with advanced AI capabilities[1][2][5][7].

Citations:
[1] https://impactum.mx/enhancing-your-applications-with-open-ai-the-ultimate-guide-to-api-integration/
[2] https://impactum.mx/mastering-open-ai-api-integration-a-step-by-step-tutorial-for-beginners/
[3] https://github.com/solygambas/python-openai-projects
[4] https://platform.openai.com/docs/quickstart
[5] https://wesoftyou.com/ai/how-to-build-a-native-openai-integration/
[6] https://www.reddit.com/r/OpenAI/comments/16l62m9/best_practices_for_hosting_a_website_that_plugs/
[7] https://dev.to/jehnz/integrating-openai-api-with-a-react-application-3378
[8] https://tech-stack.com/blog/open-ai-api-integration/
[9] https://dev.to/info_generalhazedawn_a3d/exploring-artificial-intelligence-with-openai-apis-integrate-gpt-into-your-web-applications-4pkm
[10] https://syndelltech.com/how-to-integrate-openai-api-into-business-app/

When handling errors in OpenAI API requests, it's crucial to implement robust error handling strategies to ensure your application remains stable and provides a smooth user experience. Here are the best practices for handling errors in OpenAI API requests:

## Implement Structured Error Handling

Use a try-except block to catch and handle specific types of errors:

```python
import openai
from openai import OpenAI

client = OpenAI()

try:
    response = client.chat.completions.create(
        prompt="Hello world",
        model="gpt-4o-mini"
    )
except openai.APIError as e:
    print(f"OpenAI API returned an API Error: {e}")
except openai.APIConnectionError as e:
    print(f"Failed to connect to OpenAI API: {e}")
except openai.RateLimitError as e:
    print(f"OpenAI API request exceeded rate limit: {e}")
```

## Handle Specific Error Types

Catch and handle different types of errors separately to provide more granular control:

- `APIError`: General API errors
- `APIConnectionError`: Network-related issues
- `RateLimitError`: Exceeding API rate limits
- `AuthenticationError`: Invalid API credentials
- `InvalidRequestError`: Malformed requests or invalid parameters

## Implement Retry Logic

For transient errors, especially rate limit errors, implement a retry mechanism with exponential backoff:

```python
import time
import openai

def make_api_request():
    max_retries = 5
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            # Make your API request here
            return response
        except openai.RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(retry_delay)
            retry_delay *= 2
```

## Log Errors

Always log errors for debugging and monitoring purposes:

```python
import logging

try:
    # Make API request
except openai.OpenAIError as e:
    logging.error(f"OpenAI API error: {e}")
```

## Provide User Feedback

Offer meaningful feedback to users when errors occur, rather than displaying generic error messages.

## Set Request Timeouts

Implement timeouts for API requests to prevent indefinite waiting:

```python
try:
    response = client.chat.completions.create(
        prompt="Hello world",
        model="gpt-4o-mini",
        timeout=10  # Set a 10-second timeout
    )
except openai.APITimeoutError as e:
    print(f"Request timed out: {e}")
```

## Implement Circuit Breakers

Use a circuit breaker pattern to temporarily disable API calls if a high number of requests are failing consistently.

## Monitor and Alert

Set up monitoring and alerting systems to track API usage and errors, allowing for proactive issue resolution.

## Validate Inputs

Ensure that all inputs to the API are validated before making the request to prevent `InvalidRequestError`.

## Handle Rate Limits Proactively

Implement strategies to avoid hitting rate limits:

- Use batch processing for multiple requests
- Implement usage limits for individual users
- Monitor API usage and set up alerts for unusual activity

By following these best practices, you can create a more resilient application that gracefully handles errors when interacting with the OpenAI API, providing a better experience for your users and easier maintenance for developers[1][3][5][8][10].

Citations:
[1] https://www.restack.io/p/openai-python-answer-error-handling-cat-ai
[2] https://www.lunar.dev/flows/openai-api-retry-for-failed-requests
[3] https://community.openai.com/t/how-to-understand-and-handle-error-codes-from-the-openai-api/45888
[4] https://platform.openai.com/docs/guides/error-codes
[5] https://www.restack.io/p/openai-python-answer-error-handling-examples-cat-ai
[6] https://cookbook.openai.com/examples/how_to_handle_rate_limits
[7] https://campus.datacamp.com/courses/developing-ai-systems-with-the-openai-api/structuring-end-to-end-applications?ex=4
[8] https://platform.openai.com/docs/guides/safety-best-practices
[9] https://stackoverflow.com/questions/76363168/openai-api-how-do-i-handle-errors-in-python
[10] https://help.openai.com/en/articles/6897213-openai-library-error-types-guidance

The OpenAI API in Python offers a wide range of advanced use cases, enabling developers to build sophisticated AI-driven applications. Below are some advanced use cases categorized by functionality:

## **Advanced Use Cases**

### **1. Text Processing and Generation**
- **Custom Chatbots**: Build intelligent chatbots tailored for specific industries or tasks, such as customer support or virtual assistants, using the `ChatCompletion` API with models like GPT-4.
- **Content Creation**: Automate the generation of blog posts, product descriptions, or marketing copy. For example, generating SEO-optimized articles or personalized email drafts.
- **Summarization**: Summarize lengthy documents, news articles, or meeting notes into concise summaries.
- **Sentiment Analysis**: Analyze customer reviews or social media comments to determine sentiment (positive, negative, or neutral)[4][6].

### **2. Code and Development Assistance**
- **Code Generation**: Generate code snippets based on natural language descriptions. For instance, creating Python functions or SQL queries on demand.
- **Code Debugging**: Provide explanations for code errors and suggest fixes.
- **Documentation Generation**: Automatically generate documentation for codebases using comments and function descriptions[3][4].

### **3. Data Analysis and Automation**
- **Data Extraction**: Extract structured data from unstructured text (e.g., extracting names, dates, or key events from documents).
- **Automated Reporting**: Generate business reports by summarizing large datasets and providing insights in natural language.
- **Market Research**: Scrape and analyze competitor data, summarize trends, and generate actionable insights[2][6].

### **4. Multimodal Applications**
- **Image Understanding**: Use models like GPT-4V to analyze images and answer questions about them (e.g., identifying objects in images or describing scenes).
- **Image Generation**: Integrate with DALL·E to create visual content based on textual prompts[10].

### **5. Integration with External APIs**
- **Function Calling**: Enable the model to call external APIs for tasks like retrieving real-time data (e.g., weather updates) and processing it further. For example:
  - A user asks about the current weather in a city; the model triggers a weather API call and summarizes the response[5].
  
### **6. Personalization**
- **Dynamic Content Personalization**: Tailor website content or recommendations based on user preferences and behavior.
- **Personalized Email Campaigns**: Generate unique email content for leads based on their profiles[2][6].

### **7. Language Translation**
Translate text between languages while preserving context and tone. This is useful for international businesses or multilingual applications[4].

### **8. Advanced Search and Retrieval**
- **Semantic Search**: Use embeddings to implement semantic search systems that retrieve relevant documents based on meaning rather than keywords.
- **Knowledge Base Querying**: Build systems that can answer questions by querying structured knowledge bases[7].

### **9. Creative Applications**
- **Storytelling and Game Design**: Generate storylines, character dialogues, or world-building elements for games and interactive media.
- **Poetry and Art Creation**: Produce creative outputs like poems or visual art concepts[6][10].

## **Implementation Tips**
To get started with these use cases:
1. Install the OpenAI Python library:
   ```bash
   pip install openai
   ```
2. Authenticate using your API key:
   ```python
   import openai
   openai.api_key = "YOUR_API_KEY"
   ```
3. Use appropriate models (e.g., `gpt-4`, `gpt-3.5-turbo`) depending on your task requirements.

By leveraging these advanced use cases, developers can unlock the full potential of OpenAI's API to create innovative solutions across industries such as marketing, software development, customer service, and more.

Citations:
[1] https://www.geeksforgeeks.org/openai-python-api/
[2] https://www.reddit.com/r/OpenAI/comments/16le9sb/what_are_people_using_the_openai_apis_for/
[3] https://www.doprax.com/tutorial/a-step-by-step-guide-to-using-the-openai-python-api/
[4] https://www.newhorizons.com/resources/blog/the-complete-guide-for-using-the-openai-python-api
[5] https://arize.com/blog-course/mastering-openai-api-tips-and-tricks/
[6] https://www.sitepoint.com/python-build-ai-tools-openai-api/
[7] https://platform.openai.com/docs/quickstart
[8] https://www.datacamp.com/tutorial/gpt4o-api-openai-tutorial
[9] https://github.com/openai/openai-quickstart-python
[10] https://www.kdnuggets.com/exploring-the-openai-api-with-python

Based on the provided code and test output, I can see the issue is with the OpenAI client initialization in newer versions of the library. Let me help address this:

1. **OpenAIService Fix**:
The error occurs because the OpenAI client is trying to pass a `proxies` parameter that's no longer supported. Here's how we should modify the OpenAIService initialization:

```python
def __init__(self, api_key: Optional[str] = None):
    """Initialize OpenAI service.
    
    Args:
        api_key: Optional API key (defaults to settings.OPENAI_API_KEY)
        
    Raises:
        AIServiceError: If API key is not found in settings or environment
    """
    settings = get_settings()
    self.api_key = api_key or settings.OPENAI_API_KEY
    if not self.api_key:
        raise AIServiceError("OpenAI API key not found in settings or environment")
    
    self.model = settings.OPENAI_MODEL
    self.max_retries = settings.OPENAI_MAX_RETRIES
    self.retry_delay = settings.OPENAI_RETRY_DELAY
    
    try:
        # Initialize with minimal parameters
        self.client = OpenAI(
            api_key=self.api_key,
        )
        # Set timeout and other configurations directly if needed
        self.client.timeout = 30.0  # Optional: Set custom timeout
    except Exception as e:
        raise AIServiceError(f"Failed to initialize OpenAI client: {str(e)}")
```

2. **Integration Test Updates**:
Let's modify the integration tests to include better error handling:

```python
@pytest.mark.integration
class TestOpenAIServiceIntegration:
    """Integration tests for OpenAIService."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for integration tests."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set in environment")
        # Verify API key format
        if not api_key.startswith(('sk-', 'dummy-key-for-test')):
            pytest.skip("Invalid OPENAI_API_KEY format")
        yield

    def test_generate_route_fact_integration(self):
        """Integration test for route fact generation."""
        try:
            service = OpenAIService()
            origin = Location(address="Berlin, Germany", latitude=52.5200, longitude=13.4050)
            destination = Location(address="Warsaw, Poland", latitude=52.2297, longitude=21.0122)
            result = service.generate_route_fact(origin, destination)
            assert isinstance(result, str)
            assert len(result) > 0
        except AIServiceError as e:
            pytest.fail(f"Integration test failed: {str(e)}")

    def test_enhance_route_description_integration(self):
        """Integration test for route description enhancement."""
        try:
            service = OpenAIService()
            origin = Location(address="Berlin, Germany", latitude=52.5200, longitude=13.4050)
            destination = Location(address="Warsaw, Poland", latitude=52.2297, longitude=21.0122)
            result = service.enhance_route_description(origin, destination, 500.0, 6.5)
            assert isinstance(result, str)
            assert len(result) > 0
        except AIServiceError as e:
            pytest.fail(f"Integration test failed: {str(e)}")
```

3. **Configuration Recommendation**:
Your config.py looks good, but let's add a pytest marker for integration tests to avoid warnings:

```python
# In pytest.ini or pyproject.toml
[tool.pytest.ini_options]
markers = [
    "integration: marks tests as integration tests",
]
```