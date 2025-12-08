package main

import (
	"log"
	"os"
	"github.com/bwmarrin/discordgo"
	"github.com/rajathjn/frostmourne_tunes/internal/utils"
)

// load .env file in configs folder to get DISCORD_TOKEN
const ENV_FILE string = "configs/.env"

func main() {
    err := utils.LoadEnvFile(ENV_FILE)
    if err != nil {
        log.Fatalf("Error loading .env file: %v", err)
        return
    }

    DISCORD_TOKEN := os.Getenv("DISCORD_TOKEN")

    // Create a new Discordgo session
	music_bot, err := discordgo.New("Bot " + DISCORD_TOKEN)
	if err != nil {
		log.Fatalf("Error creating Discord session: %v", err)
		return
	}

    log.Println("Welcome to Frostmourne Tunes!")

    // Hello World message sent by bot
    music_bot.Open()
    defer music_bot.Close()

    _, err = music_bot.ChannelMessageSend("1081885596227739692", "Hello World!")
    if err != nil {
        log.Fatalf("Error sending message: %v", err)
        return
    }
    

}
