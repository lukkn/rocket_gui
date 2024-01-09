class CircularBuffer {
    constructor(capacity) {
        this.capacity = capacity;
        this.data = new Array(capacity);
        this.size = 0;
        this.head = 0; // Points to the oldest element
        this.tail = 0; // Points to the next available slot
    }

    push(element) {
        if (this.size < this.capacity) {
            // Buffer is not full
            this.size++;
        } else {
            // Buffer is full, move head to the next oldest element
            this.head = (this.head + 1) % this.capacity;
        }

        // Add the new element to the buffer
        this.data[this.tail] = element;
        this.tail = (this.tail + 1) % this.capacity;
    }

    getData() {
        // Return the circular buffer data
        const result = [];
        for (let i = 0; i < this.size; i++) {
            result.push(this.data[(this.head + i) % this.capacity]);
        }
        return result;
    }
}



// Example usage
const bufferSize = 50;
const circularBuffer = new CircularBuffer(bufferSize);

// Pushing data points
for (let sensorValue = 1; sensorValue <= 70; sensorValue++) {
    circularBuffer.push(sensorValue);
}

// Retrieving data
const dataArray = circularBuffer.getData();
console.log(dataArray);
