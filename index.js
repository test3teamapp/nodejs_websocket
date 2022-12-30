const express = require("express");
const app = express();
const path = require('path');
const http = require("http");
const server = http.createServer(app);
const crypto = require("crypto");
// function alias
const randomId = () => crypto.randomBytes(8).toString("hex");

// templates for views
const pug = require("pug");

const io = require("socket.io")(server, {
  cors: {
    origin: "http://158.101.171.124:3000",
    methods: ["GET", "POST"]
  }
});

const mongoose = require("mongoose");
const UserModel = require("./models/user.js");
const SessionModel = require("./models/session.js");

main().catch((err) => console.log(err));

async function main() {
  console.log("Hello world");
  await mongoose.connect("mongodb://localhost:27017/webchatroom");
}

if (require.main === module) {
  main();
}

app.set("views", __dirname + "/views");

var singleSocket = null


app.get("/", (req, res) => {
  //res.send('<h1>Hello world</h1>');
  res.sendFile(__dirname + "/login.html");
});

app
  .route("/private/*")
  .get(function (req, res, next) {
    const sessionID = req.query.sessionid;
    const userID = req.query.userid;
    if (sessionID != null) {
      // find existing session
      SessionModel.findOne({ sessionid: sessionID, userid: userID }).lean().exec((err, session) => {
        if (err) {
          console.log("Error while searching for existing session: " + err);
          //res.sendFile(__dirname + "/login.html");
          res.send("unathorised access");
        } else if (session != null) {
          console.log(session.username + " / " + session.sessionid);
          console.log("found session for accessing '/private/*' route");
          res.sendFile(path.join(__dirname, "/private/index.html"));
          //io.emit("userinfo", userID );

        } else {
          console.log("did not find session");
          //res.sendFile(__dirname + "/login.html");
          res.send("unathorised access");
        }

      })
    } else {
      console.log("sessionID is null. unathorised access");
      // res.sendFile(__dirname + "/login.html");
      res.send("unathorised access");
    }
  })

// for serving the frame received by TCPReceiver
app
  .route("/pyimagetransfer")
  .get(function (req, res, next) {
    res.sendFile(path.join(__dirname, "/pyimagetransfer/frames/frame.jpg"));
  })

  .post(function (req, res, next) {
    // maybe add a new event...
  });

io.on("connection", (socket) => {

  if (singleSocket == null) {
    singleSocket = socket
  } else {
    socket.sessionID = singleSocket.sessionID;
    socket.userID = singleSocket.userID;
    socket.username = singleSocket.username;
    singleSocket = socket
  }

  console.log("a socket connected : " + socket.id);;

  socket.on("disconnect", () => {
    console.log("socket disconnected : " + socket.username);
    io.emit("chatmsg", "user " + socket.username + " left chat");
    io.emit("disconnect_user", socket.username); // send notice to messages window to close 
    // delete all session records for this user. 
    //ONLY ONE LOGIN IS POSSIBLE
    SessionModel.deleteMany({ username: socket.username }, function (err, result) {
      //console.log("socket disconnect, delete session result: " + result.n + " " + result.ok + " " + result.deletedCount); 
      if (err) {
        console.log("Error while deleting existing session: " + err);
      } else if (result.deletedCount > 0) {
        console.log("deleted " + result.deletedCount + " session(s)");
      } else {
        console.log("did not delete any session");
      }

    });
    socket = null;
    singleSocket = null;
  });


  socket.on("chatmsg", (msg) => {
    console.log("message from : " + socket.username + " = " + msg);
    io.emit("chatmsg", socket.username + " --> " + msg);
  });

  socket.on("logininfo", (msg) => {
    //console.log("login from : " + socket.id + " = " + msg);
    const username = msg.split("/")[0];
    const password = msg.split("/")[1];
    if (!username) {
      console.log("no username");
      socket.disconnect();
      return next(new Error("invalid username"));
    }

    // TODO CHECK USERNAME
    // use lean() to have imediate access to the properties of the user object found
    UserModel.findOne({ username: username }).lean().exec((err, user) => {
      if (err) {
        console.log("Error while searching for existing user: " + err);
        socket.disconnect();
        return new Error("db error");
      } else if (user != null) {
        //console.log(user.username + " / " + user.password);
        var possibleUser = new UserModel({
          username: user.username,
          password: user.password
        });
        possibleUser.comparePassword(password, function (error, isMatch) {
          if (error != null) {
            console.log("Error when checking password");
            socket.disconnect();
            return new Error("db error");
          } else {
            if (isMatch) {
              console.log("Username/Password ok");
              // create new session
              socket.sessionID = randomId();
              socket.userID = randomId();
              socket.username = username;
              // persist session
              const sess = new SessionModel({
                username: username,
                userid: socket.userID,
                sessionid: socket.sessionID
              });
              sess.save(function (err) {
                if (err) return handleError(err);
                // saved!
              });

              socket.emit("loggedin", socket.sessionID, socket.userID);
              console.log("Logged in: " + socket.username);
            } else {
              console.log("Username/Password missmatch");
              socket.disconnect();
              return new Error("Username/Password missmatch");
            }
          }
        })
      } else {
        console.log("non existing user");
        socket.disconnect();
        return new Error("non existing user");
      }
    });
  });

  socket.on("request_session_info", () => {
    console.log("session info requested");
    io.emit("session_info", socket.username, socket.userID, socket.sessionID);
  });


  socket.on("error", (err) => {
    console.log("ERROR : " + err.message);
    if (err && err.message === "unauthorized event") {
      socket.disconnect();
    }
  });
});

server.listen(3000, () => {
  console.log("chat nodejs server listening on *:3000");
});
