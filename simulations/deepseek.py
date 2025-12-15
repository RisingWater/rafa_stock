# deepseek.py
import requests
import json
import logging
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

load_dotenv()

class DeepSeekAPI:
    def __init__(self):
        self._api_key = os.environ.get("DEEPSEEK_API_KEY")
        self.token_cost = 0
    
    def ask_question(self, prompt, model="deepseek-chat", timeout=60):
        """
        Send question to DeepSeek API and get response
        
        Args:
            prompt (str): The question or prompt to send
            model (str): Model to use
            timeout (int): Request timeout in seconds
            
        Returns:
            str: API response content, or None if failed
        """
        if not self._api_key:
            error_msg = "DeepSeek API key not configured"
            logger.error(error_msg)
            return None
        
        try:
            url = "https://api.deepseek.com/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}"
            }
            
            data = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False
            }
            
            logger.info("Sending request to DeepSeek API...")
            
            response = requests.post(url, headers=headers, json=data, timeout=timeout)
            
            if response.status_code == 200:
                result = response.json()
                self.token_cost = result["usage"]["total_tokens"]
                logger.info(f"消耗token数: {result['usage']['total_tokens']}")
                content = result["choices"][0]["message"]["content"]
                logger.info("DeepSeek API request successful")
                return content
            else:
                logger.error(f"DeepSeek API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error calling DeepSeek API: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error calling DeepSeek API: {str(e)}")
            return None
    
# Test function
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    logger.info("Testing DeepSeek API...")
    
    deepseek = DeepSeekAPI()
        
    # Test with a simple question
    test_prompt = "请用一句话介绍你自己"
    logger.info(f"\nTesting with prompt: {test_prompt}")
    
    response = deepseek.ask_question(test_prompt)
    if response:
        logger.info(f"Response: {response}")
    else:
        logger.info("Failed to get response from DeepSeek API")
