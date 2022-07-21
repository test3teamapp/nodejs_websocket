const mongoose = require("mongoose");
const bcrypt = require("bcryptjs");

const SessionSchema = new mongoose.Schema({
  username: String,
  userid: String,
  sessionid: String
});

module.exports = mongoose.model("Session", SessionSchema);
