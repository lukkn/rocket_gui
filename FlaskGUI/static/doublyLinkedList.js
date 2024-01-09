class doublyLinkedList {
    constructor(capacity) {
        this.capacity = capacity;
        this.size = 0;
        this.head = null; 
        this.tail = null; 
        this.min = null;
        this.max = null;
    }

    popFirst(){
        // if the current min/max value was popped, find new min/max\
        if (this.head.value == this.max || this.head.value == this.max ){
            this.findMinMax();
        }

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

        this.updateMinMax(value);

        // if the list is full, remove the oldest element
        if (this.size >= this.capacity){
            this.popFirst();
        }

        // if the list is empty, set new node as head. If not, set the next node of the previous tail to new node.
        if (this.head == null){
            this.head = newNode;
            this.max = value;
            this.min = value;
        } else {
            this.tail.next = newNode;
        }
    
        this.tail = newNode;
        this.size ++;
    }  

    updateMinMax(value){
        if (value > this.max){
            this.max = value;
        } 
        if (value < this.min) {
            this.min = value;
        }
    }
    
    findMinMax(){
        var currentNode = this.head;
        var tempMax = -Infinity;
        var tempMin = Infinity;
        while (currentNode != null){
            if (currentNode.value > tempMax){
                tempMax = currentNode.value;
            }
            if (currentNode.value < tempMin) {
                tempMin = currentNode.value;
            }
            currentNode = currentNode.next;
        }
        this.max = tempMax;
        this.min = tempMin;
    }
    
}

class Node {
    constructor(value){
        this.value = value;
        this.next = null;
        this.previous = null;
    }
}