package com.example.kafkademo;

/**
 * 订单事件：演示用的最简领域对象。
 *
 * 说明：生产环境建议用 Avro / Protobuf + Schema Registry，JSON 只是入门阶段的折中——
 * 它没有 schema 演进约束，字段改名/删字段会直接把消费者打挂。
 */
public class OrderEvent {

    private String orderId;
    private String userId;
    private long amount;
    /** 故意留一个字段来演示消费失败与死信：为 true 时消费者抛异常 */
    private boolean poison;

    public OrderEvent() {
    }

    public OrderEvent(String orderId, String userId, long amount, boolean poison) {
        this.orderId = orderId;
        this.userId = userId;
        this.amount = amount;
        this.poison = poison;
    }

    public String getOrderId() {
        return orderId;
    }

    public void setOrderId(String orderId) {
        this.orderId = orderId;
    }

    public String getUserId() {
        return userId;
    }

    public void setUserId(String userId) {
        this.userId = userId;
    }

    public long getAmount() {
        return amount;
    }

    public void setAmount(long amount) {
        this.amount = amount;
    }

    public boolean isPoison() {
        return poison;
    }

    public void setPoison(boolean poison) {
        this.poison = poison;
    }

    @Override
    public String toString() {
        return "OrderEvent{orderId='" + orderId + "', userId='" + userId + "', amount=" + amount + ", poison=" + poison + '}';
    }
}
