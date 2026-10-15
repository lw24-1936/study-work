package com.example.demo;

import jakarta.validation.constraints.NotBlank;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

@RestController
@RequestMapping("/api/todos")
public class TodoController {

    public record Todo(long id, String title, boolean done) {
    }

    public record CreateTodoRequest(@NotBlank String title) {
    }

    private final Map<Long, Todo> store = new ConcurrentHashMap<>();
    private final AtomicLong seq = new AtomicLong();

    @GetMapping
    public List<Todo> list() {
        return new ArrayList<>(store.values());
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public Todo create(@RequestBody @jakarta.validation.Valid CreateTodoRequest req) {
        long id = seq.incrementAndGet();
        Todo todo = new Todo(id, req.title(), false);
        store.put(id, todo);
        return todo;
    }

    @PutMapping("/{id}")
    public ResponseEntity<Todo> toggle(@PathVariable long id) {
        Todo existing = store.get(id);
        if (existing == null) {
            return ResponseEntity.notFound().build();
        }
        Todo updated = new Todo(existing.id(), existing.title(), !existing.done());
        store.put(id, updated);
        return ResponseEntity.ok(updated);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable long id) {
        return store.remove(id) == null
                ? ResponseEntity.notFound().build()
                : ResponseEntity.noContent().build();
    }

    @GetMapping("/health")
    public Map<String, Object> health() {
        return Map.of("status", "UP", "size", store.size());
    }
}
