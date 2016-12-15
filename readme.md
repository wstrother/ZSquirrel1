# Welcome to ZSquirrel1!

"ZSquirrel1" is the name of an open source 2D games API that I am writing in Python 3, currently on a Pygame (SDL) based back end. The "1" on the end is part of the name of the API, not a version number. This is intentional and has no purpose. I hereby publish it under GPL, non-commercial share alike, although stand-alone derivate products (i.e. games or software made using the API) are waived of the non-commercial reservation (Subject to my discretion, ask if you have questions).

This is currently a pre-Alpha build, so some features this readme talks about may not be fully implemented at the time you are accessing this repo. I will strive to keep my progress-levels and issues lists up to date as I continue development.

## What is ZSquirrel1?

In this repository you will find a collection of modules, starting resources and configuration files for use in developing 2D games using compiled Python classes, as well as a set of graphical utilities to aid in the devlopment of those Python classes.  Currently, the only dependency besides Python 3 is Pygame. I have some interest in potentially porting the backend in the future (There's a library called PySDL2 that is essentially an update to Pygame which looks promising) but that's not a huge concern for the immediate future.

*As a matter of aesthetic choice* this particular API caters to a low-resolution, pseudo-retro vaguely 16-bit "style" of game design so features that are not really central to that type of development will largely be ignored. (Or at least for the foreseeable future. Networking support would be awesome but it's probably something that will be outside my level of expertise for a while.) Support for 3D rendering and high-resolution surfaces is not something that I feel fits in with the design philosophy of this API.

## What is the Goal?

I have a number of goals with this API. I've noticed because Python is an easy language to learn there's a lot of beginner-level interest in the Pygame platform as a tool for learning to program games, however the Pygame package is not really a fully developed API, just a wrapper for the SDL library essentially. There's a lot of good tutorial material specific to developing with Pygame but it's mostly treated with the "just make stuff appear on the screen" approach. This is a great way to dive into learning programming and feel good about what you can do with it, (indeed this is largely how I started developing this API) but there isn't, in my humble opinion, nearly enough emphasis on building flexible, extensible code with an elegant, simple to use interface.

Learning to do it yourself is a great approach, and how I came up with the idea to build my own API, but I've put so much time and work into it now, I think it would be prudent to help share with people what I've learned, as well as invite people to work on the same problems I'm working at and see if they can come up with a better approach than I can. There are a lot of common problems that don't need to be solved over and over again and the main goal of this API is to hammer out the best general-use approach to each solution, as well as some more context specific implementations that can build on those general-use approaches.

### Specific features / planned feature goals

* **Powerful event-delegation API for controlling Python class instances** - The ZSquirrel1 events module defines an interface for controlling instances of your Python classes through chainable, deferred method calls. The module and API allows for integration of "event requests" with a flexible syntax that can translate entirely hashable "query" arguments into Event objects for use by the engine's EventHandler class. The event request syntax on its own has built in support for chained method calls, time delays and interpolation, and even conditional behavior. Because queries can be entirely hashable they can easily be imported from a neutral data format and interpreted by the engine.
	* **Estimated progress:** 95%

* **Platform/device-agnostic controller support** - ZSquirrel1 allows for the use of "templates" that are used to build a virtual controller object in Python. The built in utilities provide support for creating a "profile" of input mappings that can be used to control the virtual controller. You should be able to develop your project in such a way that the "player" has maximum flexibility for mapping input devices while your project code itself just works irrespective of what the player has hooked up to their computer.
	* **Estimated progress:** 95%

* **Developer-friendly Menu/GUI support** - ZSquirrel1 has built in classes for developing "Menu" and other GUI objects based on minimal specifications by the developer. Project style-sheets can control the look and feel of GUI elements, while the use of the "MenuTools" mini-API provides a straight-forward functional approach to menuing behavior. Also for those with less experience in functional UI programming, a library of pre-built context-sensitive menus can be imported where appropriate and controlled by project configuration files.
	* **Estimated progress:** 70%

* **Easy Stylesheet/Resource library management** - ZSquirrel1 automatically builds stylesheet and resource-library objects based on config files that allow contextual control of game environments and elements.
	* **Estimated progress:** 90%

* **Simple custom-implementation of physics / collision regimens** - Project configuration will allow a simple way to effectively customize the physics and collision behaviors of any game environment, even allowing multiple configurations per project in different contexts. In addition to controlling simple environment parameters like gravity and collision elasticity, the API will define a basic set of guidelines for fine tuning the exact implementation of different regimens for handling physics and collisions in different contexts. I.E. should sprites have instantaneous velocities or derive velocity by integrating acceleration forces? Should sprite-sprite collisions employ a certain collision algorithm while sprite-map region collisions use another? Etc.
	* **Estimated progress:** 20%

* **Maximum re-usability of animation / state-machine configurations** - The ZSquirrel1 API will provide a framework for customizing and re-using sprite animation/behavior state logic as well as providing usable examples out of the box that can be customized and applied in a variety of contexts.
	* **Estimated progress:** 0%

* **Layered Game environments with built in scaling/scrolling** - ZSquirrel1 provides source code for game environment objects with built in support of scaled/zoomable displays, as well as a number of scrolling paradigms, including built in parallax/interpolation support.
	* **Estimated progress:** 10%

* **Dynamic sprite-sheet generation / graphical utilities** - ZSquirrel1 will provide a set of tools for customizing dynamic generation of spritesheets including merging different "layer" graphics and intuitive HSV based controls for palette-shifting. *This feature will probably utilize an outside library and is not yet implemented.*
	* **Estimated progress:** 0%

* **Integrated support for xml tilemaps** - ZSquirrel will provide basic integration support for the common .tmx format. *This feature will probably utilize an outside library and is not yet implemented.*
	* **Estimated progress:** 0%


### Known Issues

* Multi-threading needs to be implemented for any GUI elements that call a method with a while loop (TextField objects and the InputMapper class) so as not to break the game engine object's main method while loop.
