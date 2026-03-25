class PaymentProcessor{
    public void process(int amount){
        verify_funds(amount);
        System.out.println("Processed");
    }
}