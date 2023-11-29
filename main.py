# CSE 120 Simple Game Final Project
# Created by John Mejia

import arcade
import random

# Window constants

SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
SCREEN_TITLE = "Dodge the bullets!!"

# Constants used to scale our sprites and movement
CHARACTER_SCALING = 1
TILE_SCALING = 2.09

# Player movement speed and gravity
PLAYER_MOVEMENT_SPEED = 10
GRAVITY = 1
PLAYER_JUMP_SPEED = 30

# Constants used to track if the player is facing left or right
RIGHT_FACING = 0
LEFT_FACING = 1

LAYER_NAME_PLAYER = "Player"


def load_texture_pair(filename):
    """
    Load a texture pair, with the second being a mirror image.
    """
    return [
        arcade.load_texture(filename),
        arcade.load_texture(filename, flipped_horizontally=True),
    ]


class PlayerCharacter(arcade.Sprite):
    """Player Sprite"""

    def __init__(self):

        # Set up parent class
        super().__init__()

        # Default to face-right
        self.character_face_direction = RIGHT_FACING

        # Used for flipping between image sequences
        self.cur_texture = 0
        self.scale = CHARACTER_SCALING

        # Track our state
        self.jumping = False

        # --- Load Textures ---
        main_path = "Sprites/Dude_Monster/Dude_Monster"

        # Load textures for idle standing
        self.idle_texture_pair = load_texture_pair(f"{main_path}_Idle_0.png")
        self.jump_texture_pair = load_texture_pair(f"{main_path}_jump.png")
        self.fall_texture_pair = load_texture_pair(f"{main_path}_fall.png")

        # Load textures for running
        self.run_textures = []
        for i in range(6):
            texture = load_texture_pair(f"{main_path}_Run_{i}.png")
            self.run_textures.append(texture)

        # Set the initial texture
        self.texture = self.idle_texture_pair[0]

        # Hit box will be set based on the first image used. If you want to specify
        # a different hit box, you can do it like the code below.
        # set_hit_box = [[-22, -64], [22, -64], [22, 28], [-22, 28]]
        self.hit_box = self.texture.hit_box_points

    def update_animation(self, delta_time: float = 1 / 60):

        # Figure out if we need to flip face left or right
        if self.change_x < 0 and self.character_face_direction == RIGHT_FACING:
            self.character_face_direction = LEFT_FACING
        elif self.change_x > 0 and self.character_face_direction == LEFT_FACING:
            self.character_face_direction = RIGHT_FACING

        # Jumping animation
        if self.change_y > 0:
            self.texture = self.jump_texture_pair[self.character_face_direction]
            return
        elif self.change_y < 0:
            self.texture = self.fall_texture_pair[self.character_face_direction]
            return

        # Idle animation
        if self.change_x == 0:
            self.texture = self.idle_texture_pair[self.character_face_direction]
            return

        # Walking animation
        self.cur_texture += 1/2
        if self.cur_texture > 5:
            self.cur_texture = 0
        self.texture = self.run_textures[int(self.cur_texture)][
            self.character_face_direction
        ]


class MyGame(arcade.Window):
    def __init__(self):
        # Call to set up the window
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        # The TileMap Object
        self.tile_map = None

        # The Scene object
        self.scene = None

        # Variable that holds player sprite
        self.player_sprite = None

        # Our physics engine
        self.physics_engine = None

        # Camera to hold GUI elements
        self.gui_camera = None

        # Score tracker
        self.score = 0

        # Variable that holds the odds for a bullet to spawn
        # 1 in 60 in this case
        self.odds = 60

        # Load sounds
        self.game_over = arcade.load_sound(":resources:sounds/hurt3.wav")
        self.jump_sfx = arcade.load_sound(":resources:sounds/phaseJump1.ogg")
        self.impact_sfx = arcade.load_sound(":resources:sounds/hit1.wav")

        # Check if we need to reset the score
        self.reset_score = True

        # List for bullets
        self.bullet_list = None

        # Track the current state of what key is pressed
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False

        arcade.set_background_color(arcade.csscolor.BLACK)

    def setup(self):

        # Set up sprite list for bullets
        self.bullet_list = arcade.SpriteList()

        # Setup GUI camera
        self.gui_camera = arcade.Camera(self.width, self.height)

        # Name of the map file to load
        map_name = "TileMaps/MainMap.json"

        # Layer options for collision
        layer_options = {
            "Collision": {
                "use_spacial_hash": True
            }
        }

        # Read the TileMap
        self.tile_map = arcade.load_tilemap(map_name, TILE_SCALING, layer_options)

        # Initialize Scene with our TileMap
        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        # Score tracker
        self.score = 0

        # Set up player sprite
        self.player_sprite = PlayerCharacter()
        self.player_sprite.center_x = 800
        self.player_sprite.center_y = 400
        self.scene.add_sprite(LAYER_NAME_PLAYER, self.player_sprite)

        # Set background color
        if self.tile_map.background_color:
            arcade.set_background_color(self.tile_map.background_color)

        # Create the 'physics engine'
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, gravity_constant=GRAVITY, walls=self.scene["Collision"]
        )

    def on_draw(self):
        # function to render screen
        self.clear()

        # draw our scene
        self.scene.draw()

        # Activate the GUI camera before drawing GUI elements
        self.gui_camera.use()

        # Draw our score on the screen, scrolling it with the viewport
        score_text = f"Score: {self.score}"
        arcade.draw_text(
            score_text,
            10,
            870,
            arcade.csscolor.WHITE,
            20,
        )

        # Draw our bullets
        self.bullet_list.draw()

    def update_player_speed(self):

        # Calculate speed based on the keys pressed
        self.player_sprite.change_x = 0
        self.player_sprite.change_y = 0

        if self.up_pressed and not self.down_pressed:
            self.player_sprite.change_y = PLAYER_JUMP_SPEED
        elif self.down_pressed and not self.up_pressed:
            self.player_sprite.change_y = -PLAYER_MOVEMENT_SPEED
        if self.left_pressed and not self.right_pressed:
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
        elif self.right_pressed and not self.left_pressed:
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed."""

        if key == arcade.key.SPACE:
            self.up_pressed = True
            if self.physics_engine.can_jump():
                arcade.play_sound(self.jump_sfx)
                self.update_player_speed()
            # Change to false after jump to avoid users to be able to jump midair
            self.up_pressed = False
        elif key == arcade.key.S:
            self.down_pressed = True
            self.update_player_speed()
        elif key == arcade.key.A:
            self.left_pressed = True
            self.update_player_speed()
        elif key == arcade.key.D:
            self.right_pressed = True
            self.update_player_speed()

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key."""

        if key == arcade.key.SPACE:
            self.up_pressed = False
            self.update_player_speed()
        elif key == arcade.key.S:
            self.down_pressed = False
            self.update_player_speed()
        elif key == arcade.key.A:
            self.left_pressed = False
            self.update_player_speed()
        elif key == arcade.key.D:
            self.right_pressed = False
            self.update_player_speed()

    def on_update(self, delta_time):
        """Movement and game logic"""

        # Move the player with the physics engine
        self.physics_engine.update()

        # Update Animations
        self.scene.update_animation(
            delta_time, [LAYER_NAME_PLAYER]
        )

        # Resets player position, score, and bullet odds when fall from map is detected
        if self.player_sprite.center_y < -100:
            self.player_sprite.center_x = 800
            self.player_sprite.center_y = 400
            self.score = 0
            self.odds = 60
            arcade.play_sound(self.game_over)

        # Logic for bullet spawning
        # Adjust odds as time goes on
        self.odds -= 1/480
        if self.odds < 1:
            self.odds = 1

        if random.randrange(int(self.odds)) == 0:
            bullet = arcade.Sprite(":resources:images/space_shooter/laserRed01.png")
            bullet.center_x = random.randrange(1, 1600)
            bullet.angle = 180
            bullet.top = 900
            bullet.change_y = -7
            self.bullet_list.append(bullet)

        # Get rid of bullet when it flies off-screen and check for collision
        # Resets player position, score, and bullet odds when collision is detected
        for bullet in self.bullet_list:
            player_hit = arcade.check_for_collision(bullet, self.player_sprite)
            if player_hit:
                bullet.remove_from_sprite_lists()
                self.player_sprite.center_x = 800
                self.player_sprite.center_y = 400
                self.score = 0
                self.odds = 60
                arcade.play_sound(self.impact_sfx)

            if bullet.top < 0:
                bullet.remove_from_sprite_lists()

        self.bullet_list.update()

        # Increase score as time goes on
        self.score += 1


def main():
    window = MyGame()
    window.setup()
    arcade.run()


if __name__ == '__main__':
    main()
