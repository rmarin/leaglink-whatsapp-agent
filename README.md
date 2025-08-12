# Legalink WhatsApp Agent

A FastAPI-based WhatsApp webhook integration powered by LangGraph and Claude 4 for providing Colombian labor law assistance. This intelligent agent can understand legal questions in Spanish and provide accurate information about Colombian labor legislation. Lambda using CloudFormation.

## Features

- **Intelligent Legal Assistant**: LangGraph-powered agent specialized in Colombian labor law
- **Claude 4 Integration**: Advanced AI responses using Anthropic's Claude 4
- **Spanish Language Support**: Native Spanish conversation handling
- **WhatsApp Integration**: Seamless WhatsApp Cloud API webhook integration
- **Conversation Memory**: Maintains context across multiple messages
- **Legal Topic Classification**: Automatically identifies legal topics and provides relevant information
- **AWS Lambda Deployment**: Serverless deployment using CloudFormation
- **RESTful API**: FastAPI-based architecture with comprehensive endpoints

## Project Structure

```
├── app/
│   ├── __init__.py
│   ├── main.py           # Main FastAPI application
│   ├── agent/            # Colombian Labor Law Agent
│   │   ├── __init__.py
│   │   ├── state.py      # Agent state management
│   │   ├── nodes.py      # LangGraph workflow nodes
│   │   ├── workflow.py   # Main agent workflow
│   │   ├── prompts.py    # Claude 4 prompt templates
│   │   └── knowledge.py  # Colombian labor law knowledge base
│   └── api/
│       ├── __init__.py
│       ├── messages.py   # Messages endpoints
│       └── webhook.py    # WhatsApp webhook with agent integration
├── infrastructure/
│   └── template.yaml     # CloudFormation template
├── .venv/                # Virtual environment (created by uv)
├── main.py               # Entry point for local development
├── requirements.txt      # Project dependencies
├── deploy.sh             # Deployment script
└── README.md             # This file
```

## Colombian Labor Law Agent

The heart of this application is an intelligent agent built with LangGraph that specializes in Colombian labor law. The agent can:

### Capabilities
- **Legal Topic Classification**: Automatically identifies the type of legal question (contracts, wages, termination, etc.)
- **Contextual Responses**: Maintains conversation history for better context understanding
- **Spanish Language Processing**: Native Spanish conversation handling with legal terminology
- **Legal Citations**: References relevant articles from the Colombian Labor Code when applicable
- **Conversation Memory**: Remembers previous interactions for follow-up questions

### Supported Topics
- Contratos de trabajo (Employment contracts)
- Salarios y prestaciones (Wages and benefits)
- Terminación de contratos (Contract termination)
- Derechos del trabajador (Worker rights)
- Licencias y vacaciones (Leaves and vacations)
- Seguridad social (Social security)

## Prerequisites

- Python 3.10 or higher
- uv package manager
- WhatsApp Business Account and App setup in Meta Developer Portal
- **Anthropic API Key** for Claude 4 access
- AWS CLI configured with appropriate permissions
- An S3 bucket for deployment artifacts

## Local Development

1. Copy the example environment file and configure your API credentials:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your actual credentials:
   ```bash
   WEBHOOK_VERIFY_TOKEN=your_webhook_verify_token
   GRAPH_API_TOKEN=your_whatsapp_graph_api_token
   ANTHROPIC_API_KEY=your_anthropic_api_key_for_claude4
   PORT=8080
   ```

2. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```

3. Run the application locally:
   ```bash
   python main.py
   ```

4. Access the API at http://localhost:8080
   - API documentation is available at http://localhost:8080/docs
   
5. For WhatsApp webhook testing, you'll need to expose your local server to the internet using a tool like ngrok:
   ```bash
   ngrok http 8080
   ```

## API Endpoints

- `GET /api/messages` - Get all messages
- `POST /api/messages` - Create a new message
- `GET /api/messages/{message_id}` - Get a specific message by ID
- `GET /api/webhook` - WhatsApp webhook verification endpoint
- `POST /api/webhook` - WhatsApp webhook for receiving messages

## Deployment

1. Update the S3 bucket name and AWS region in `deploy.sh`

2. Run the deployment script:
   ```bash
   ./deploy.sh
   ```

3. The script will output the API Gateway URL where your API is accessible

4. Configure your WhatsApp Cloud API webhook in the Meta Developer Portal:
   - Webhook URL: `https://your-api-gateway-url/api/webhook`
   - Verify Token: The same value you set for `WEBHOOK_VERIFY_TOKEN` in your environment
   - Subscribe to the `messages` webhook field

## Development with uv

This project uses uv for package management:

- Install a new package:
  ```bash
  uv pip install package-name
  ```

- Update requirements.txt after installing new packages:
  ```bash
  uv pip freeze > requirements.txt
  ```

## WhatsApp Cloud API Setup

1. Create a Meta Developer account and set up a WhatsApp Business App
2. Generate a Permanent Access Token for the Graph API
3. Set up a phone number for your WhatsApp Business account
4. Configure the webhook URL in the Meta Developer Portal
5. Set the appropriate environment variables in your deployment:
   - `WEBHOOK_VERIFY_TOKEN`: A secret token you define for webhook verification
   - `GRAPH_API_TOKEN`: Your WhatsApp Cloud API access token