from prompt import PromptGenerator
from deepseek import DeepSeekAPI
from simulations.stock_account_tplus1 import TPlusOneStockAccount, TradeDecision
from datetime import datetime

class DeepSeekStrategy:
    def __init__(self):
        self._deepseek_api = DeepSeekAPI()
        self._prompt_generator = PromptGenerator()

    def name(self) -> str:
        return "DeepSeek Strategy"

    def make_decision(self, stock_name: str, stock_code: str, account: TPlusOneStockAccount, cur_datetime: datetime) -> TradeDecision:
        prompt = self._prompt_generator.generate_prompt(stock_name, stock_code, account, cur_datetime)
        response = self._deepseek_api.ask_question(prompt)        
        decision = TradeDecision.from_json(response)
        return decision