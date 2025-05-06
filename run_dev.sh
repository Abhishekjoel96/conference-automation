#!/bin/bash

# Conference Networking Automation Development Script
# This script starts both the backend and frontend in development mode

# Colors for prettier output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================================${NC}"
echo -e "${GREEN}Starting Conference Networking Automation Development${NC}"
echo -e "${BLUE}=====================================================${NC}"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo -e "${YELLOW}Please create a .env file with your API keys:${NC}"
    echo "PHANTOMBUSTER_API_KEY=your-key"
    echo "SERPAPI_API_KEY=your-key"
    echo "OPENAI_API_KEY=your-key"
    echo "GOOGLE_SERVICE_ACCOUNT_FILE=path/to/credentials/service_account.json"
    exit 1
fi

# Check if credentials directory exists
if [ ! -d "credentials" ]; then
    echo -e "${YELLOW}Creating credentials directory...${NC}"
    mkdir -p credentials
    echo -e "${GREEN}Created credentials directory.${NC}"
fi

# Start backend in background
echo -e "${GREEN}Starting FastAPI backend...${NC}"

# Activate virtual environment and start the backend
source venv/bin/activate

# Save current directory
CURRENT_DIR=$(pwd)

# Start the backend from the api directory
cd "$CURRENT_DIR/api" && uvicorn index:app --reload --port 8000 &
BACKEND_PID=$!
echo -e "${GREEN}Backend running with PID: ${BACKEND_PID}${NC}"

# Wait for backend to start
echo -e "${YELLOW}Waiting for backend to start...${NC}"
sleep 3

# Start frontend - make sure we're in the correct directory
echo -e "${GREEN}Starting React frontend...${NC}"
# Use PORT=3001 to avoid conflicts with existing processes
cd "$CURRENT_DIR/frontend" && PORT=3001 npm start &
FRONTEND_PID=$!

# Print status
echo -e "${BLUE}Both services should now be running. The React development server will open in your browser.${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop both services.${NC}"

# Cleanup function
cleanup() {
    echo -e "${YELLOW}Shutting down services...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}Done!${NC}"
    exit 0
}

# Set trap for cleanup
trap cleanup INT TERM

# Wait for frontend to exit
wait $FRONTEND_PID
cleanup
