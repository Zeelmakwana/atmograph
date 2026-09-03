const express = require('express');
const app = express();
const port = 3000;

app.get('/', (req, res) => {
    res.send("Hello! Welcome to Greeting Application");
});

app.listen(port, () => {
    console.log(`Greeting app listening at http://localhost:${port}`);
});
