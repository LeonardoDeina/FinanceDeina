class MissingExchangeRateError(Exception):
    def __init__(self, from_code: str, to_code: str):
        self.from_code = from_code
        self.to_code = to_code
        super().__init__(f"Nenhuma taxa de câmbio disponível para converter {from_code} -> {to_code}")
