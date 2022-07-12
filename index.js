const express = require('express');
const app = express();
const http = require('http');
const server = http.createServer(app);
const { Server } = require("socket.io");
const io = new Server(server);

app.get('/', (req, res) => {
  //res.send('<h1>Hello world</h1>');
  res.sendFile(__dirname + '/login.html');
});

io.on('connection', (socket) => {
  console.log('a user connected : ' + socket.id);
  io.emit('chatmsg', 'user ' + socket.id + ' joined chat');

  socket.on('disconnect', () => {
    console.log('user disconnected : ' + socket.id);
    io.emit('chatmsg', 'user ' + socket.id + ' left chat');
  });

  socket.on('chatmsg', (msg) => {
    console.log('message from : '  + socket.id  + ' = ' + msg);
    io.emit('chatmsg',  socket.id  + ' --> ' + msg);
  });

  socket.on('logininfo', (msg) => {
    console.log('login from : '  + socket.id  + ' = ' + msg);
    //io.emit('chatmsg',  socket.id  + ' --> ' + msg);
  });
});

server.listen(3000, () => {
  console.log('listening on *:3000');
});