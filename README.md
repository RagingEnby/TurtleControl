# TurtleControl
TurtleControl is a project made for controlling turtles in my modded Skyblock server with friends. It contains 2 parts:
## TurtleControl Webserver
The TurtleControl webserver runs on port 8080 and allows turtles to connect to it. It then uses remote code execution to fully control a turtle remotely from Python.
## Turtle Script
The turtle script `turtle/startup.lua` contains the code that you put inside of the turtle. It will connect the webserver and listen to requests from the server. The main purpose is to remotely execute code.

# Goal
The eventual goal of this project is to use Google Gemini's tool calls to make a fully Ai controlled turtle. **THIS IS NOT USEFUL** I am literally just bored and had the idea of adding a bunch of Ai agent robots to my Skyblock world.