class PaymentProcessor:
    def process(self, amount):
        verify_funds(amount)
        print("Processed")

def verify_funds(amount):
    print("Verified")

def main():
    processor = PaymentProcessor()
    processor.process(100)