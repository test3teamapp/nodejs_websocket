const express = require("express");
const app = express();
const http = require("http");
const server = http.createServer(app);

const crypto = require("crypto");
// function alias
const randomId = () => crypto.randomBytes(8).toString("hex");

// templates for views
const pug = require("pug");


const io = require("socket.io")(server, {
  cors: {
    origin: "http://localhost:3000",
  }
});

const mongoose = require('mongoose');
main().catch(err => console.log(err));

async function main() {
  console.log("Hello world");
  await mongoose.connect('mongodb://localhost:27017/webchatroom');
}

if (require.main === module) {
  main();
}

app.set("views", __dirname + "/views");

app.get("/", (req, res) => {
  //res.send('<h1>Hello world</h1>');
  res.sendFile(__dirname + "/login.html");
});

app
  .route("/private")
  .get(function (req, res, next) {
    const sessionID = req.query.sessionid;
    if (sessionID) {
      // find existing session
      const session = sessionStore.findSession(sessionID);
      if (session) {
        console.log("found session");
        res.sendFile(__dirname + "/views/index.html");
      } else {
        console.log("did not find session");
        res.sendFile(__dirname + "/login.html");
      }
    } else {
      // no session found. send to login page
      console.log("session id not valid");
      res.sendFile(__dirname + "/login.html");
    }
  })
  .post(function (req, res, next) {
    // maybe add a new event...
  });
/*
app.get("/private", (req, res) => {
  //res.send('<h1>Hello world</h1>');
  const sessionID = socket.handshake.auth.sessionID;
  if (sessionID) {
    // find existing session
    const session = sessionStore.findSession(sessionID);
    if (session) {
      console.log("found session");
      socket.sessionID = sessionID;
      socket.userID = session.userID;
      socket.username = session.username;
      res.sendFile(__dirname + "/views/index.html");
    } else {
      res.sendFile(__dirname + "/views/login.html");
    }
  } else {
    // no session found. send to login page
    res.sendFile(__dirname + "/views/login.html");
  }
});
*/

io.on("connection", (socket) => {
  console.log("a socket connected : " + socket.id);
  io.emit("chatmsg", "user " + socket.id + " joined chat");

  socket.on("disconnect", () => {
    console.log("socket disconnected : " + socket.id);
    io.emit("chatmsg", "user " + socket.id + " left chat");
  });

  socket.on("chatmsg", (msg) => {
    console.log("message from : " + socket.id + " = " + msg);
    io.emit("chatmsg", socket.id + " --> " + msg);
  });

  socket.on("logininfo", (msg) => {
    console.log("login from : " + socket.id + " = " + msg);
    //io.emit('chatmsg',  socket.id  + ' --> ' + msg);

    const username = msg.split("/")[0];
    const password = msg.split("/")[1];
    if (!username) {
      console.log("no username");
      return next(new Error("invalid username"));
    }

    // TODO CHECK USERNAME

    // create new session
    socket.sessionID = randomId();
    socket.userID = randomId();
    socket.username = username;
    // persist session
    

    socket.emit("loggedin", socket.handshake.auth.sessionID);
  });

  socket.on("error", (err) => {
    console.log("ERROR : " + err.message);
    if (err && err.message === "unauthorized event") {
      socket.disconnect();
    }
  });
});

server.listen(3000, () => {
  console.log("listening on *:3000");
});
