class doublyLinkedList {
    constructor(capacity) {
        this.capacity = capacity;
        this.size = 0;
        this.head = null; 
        this.tail = null; 

    }

    popFirst(){
        this.head = this.head.next;
        this.head.previous = null;
        this.size --;
    }

    popLast(){
        this.tail = this.tail.previous;
        this.tail.next = null;
        this.size--;
    }

    push(value){
        const newNode = {
            value: value,
            next: null,
            previous: this.tail,
        }

        // if the list is full, remove the oldest element
        if (this.size >= this.capacity){
            this.popFirst();
        }

        // if the list is empty, set new node as head. If not, set the next node of the previous tail to new node.
        if (this.head == null){
            this.head = newNode;
        } else {
            this.tail.next = newNode;
        }
    
        this.tail = newNode;
        this.size ++;

        //updateMinMax(value);
    }  
    
}

class Node {
    constructor(value){
        this.value = value;
        this.next = null;
        this.previous = null;
    }
}