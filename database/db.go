// Да уж, когда я начинал писать эту лапшу,
// было гораздо проще ориентироваться, не то, что сейчас...
package main

import (
	"bytes"
	"encoding/gob"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"time"

	clr "github.com/Elchinchel/colorizer"
	"github.com/recoilme/pudge"
)

var cfg = &pudge.Config{SyncInterval: 1, StoreMode: 2}

var tmpcfg = &pudge.Config{SyncInterval: 15, StoreMode: 0}

var settingsDB, billing, accounts, tokenPool, usersDB *pudge.Db
var settingsTgDB, accountsTgDB, sessionTgDB *pudge.Db

var folder = "./database/files"

var backupFolders = []string{"./database/backups/one", "./database/backups/two"}

var templateCommon = "/templates_common/"
var templateDutys = "/templates_dutys/"
var templateVoice = "/templates_voice/"
var templateAnim = "/templates_anim/"

var tgStickers = "/stickers_tg/"

var quitSignal = make(chan os.Signal)

func createTemplatesFile(catalog string, uid int) error {
	var buf bytes.Buffer
	enc := gob.NewEncoder(&buf)
	enc.Encode(make([]template, 0))
	file, err := os.Create(folder + catalog + strconv.Itoa(uid))
	if err != nil {
		return err
	}
	defer file.Close()
	_, err = file.Write(buf.Bytes())
	return err
}

func writeTemplates(catalog string, uid int, data interface{}) error {
	var buf bytes.Buffer
	enc := gob.NewEncoder(&buf)
	if err := enc.Encode(data); err != nil {
		return err
	}
	file, err := os.OpenFile(folder+catalog+strconv.Itoa(uid), os.O_WRONLY, 0666)
	if err != nil {
		return err
	}
	defer file.Close()
	_, err = file.Write(buf.Bytes())
	return err
}

func readTemplates(catalog string, uid int, dataPointer interface{}) error {
	file, err := os.Open(folder + catalog + strconv.Itoa(uid))
	if err != nil {
		return err
	}
	defer file.Close()
	var buf bytes.Buffer
	for {
		bufRead := make([]byte, 1024)
		_, err := file.Read(bufRead)
		if err == io.EOF {
			break
		}
		if err != nil {
			return err
		}
		buf.Write(bufRead)
	}
	dec := gob.NewDecoder(&buf)
	err = dec.Decode(dataPointer)
	return err
}

func main() {
	log.Println("Starting DB driver...")
	var err error
	usersDB, err = pudge.Open(folder+"/users", cfg)
	if err != nil {
		log.Panic(err)
	}
	settingsDB, err = pudge.Open(folder+"/user_settings", cfg)
	if err != nil {
		log.Panic(err)
	}
	settingsTgDB, err = pudge.Open(folder+"/tg_user_settings", cfg)
	if err != nil {
		log.Panic(err)
	}
	accounts, err = pudge.Open(folder+"/user_accounts", cfg)
	if err != nil {
		log.Panic(err)
	}
	accountsTgDB, err = pudge.Open(folder+"/tg_user_accounts", cfg)
	if err != nil {
		log.Panic(err)
	}
	billing, err = pudge.Open(folder+"/balance", cfg)
	if err != nil {
		log.Panic(err)
	}
	tokenPool, err = pudge.Open(folder+"/miscellaneous", cfg)
	if err != nil {
		log.Panic(err)
	}
	sessionTgDB, err = pudge.Open(folder+"/tg_miscellaneous", cfg)
	if err != nil {
		log.Panic(err)
	}
	go mainListen()
	go backupper()
	signal.Notify(quitSignal, os.Interrupt, os.Kill) // UNIX only
	<-quitSignal
	log.Println(clr.Colorize("Shutdown DB server...", clr.Y))
	if err := pudge.CloseAll(); err != nil {
		log.Println("Pudge Shutdown err:", err)
	} else {
		log.Println(clr.Colorize("Saved!", clr.G))
	}
}

func backupper() {
	time.Sleep(60 * time.Second)
	for {
		for i, folder := range backupFolders {
			if i > 0 {
				os.Remove(backupFolders[i-1])
			} else {
				os.Remove(backupFolders[len(backupFolders)-1])
			}
			err := pudge.BackupAll(folder)
			if err == nil {
				log.Println("DB backed up in " + clr.Colorize(folder, clr.G))
			} else {
				log.Printf(clr.Colorize("DB backed up with error %s", clr.R), err)
			}
			time.Sleep(60 * time.Minute)
		}
	}
}

type serverRequest struct {
	Method     string      `json:"method"`
	Type       string      `json:"type"`
	UID        int         `json:"uid"`
	Template   templateReq `json:"template"`
	Tokens     tokensReq   `json:"tokens"`
	Account    accountReq  `json:"account"`
	Settings   settingsReq `json:"settings"`
	Value      float32     `json:"value"`
	IsTelegram bool        `json:"is_telegram"`
}

type resp struct {
	Response interface{} `json:"response"`
}

func requestHandle(c net.Conn) {
	var result []byte
	defer c.Close()
	defer func() {
		if r := recover(); r != nil {
			_, err := c.Write([]byte(`{"error":"` + fmt.Sprint(r) + `"}`))
			if err != nil {
				fmt.Println("connection writing error: ", err)
			}
			report("handler", clr.Colorize(r.(string), clr.R))
		}
	}()
	var data serverRequest
	json.NewDecoder(c).Decode(&data)
	var response interface{} = "ok"
	switch data.Method {
	case "get":
		if data.IsTelegram {
			switch data.Type {
			// case "common":
			// 	response = templateGet(templateCommon, data.UID)
			case "sticker":
				response = templateTGGet(tgStickers, data.UID)
			case "session":
				response = sessionTGGet(data.UID)
			case "settings":
				response = settingsTGGet(data.UID)
			case "account":
				response = accountTGGet(data.UID)
			}
		} else {
			switch data.Type {
			case "common":
				response = templateGet(templateCommon, data.UID)
			case "voice":
				response = templateGet(templateVoice, data.UID)
			case "dutys":
				response = templateGet(templateDutys, data.UID)
			case "anim":
				response = templateGet(templateAnim, data.UID)
			case "token":
				response = tokensGet(data.UID)
			case "settings":
				response = settingsGet(data.UID)
			case "account":
				response = accountGet(data.UID)
			}
		}
	case "set":
		if data.IsTelegram {
			switch data.Type {
			case "sticker":
				response = templateTGSet(tgStickers, data.UID, data.Template)
			}
		} else {
			switch data.Type {
			case "common":
				response = templateSet(templateCommon, data.UID, data.Template)
			case "voice":
				response = templateSet(templateVoice, data.UID, data.Template)
			case "dutys":
				response = templateSet(templateDutys, data.UID, data.Template)
			case "anim":
				response = templateSet(templateAnim, data.UID, data.Template)
			}
		}
	case "update":
		if data.IsTelegram {
			switch data.Type {
			case "session":
				sessionTGUpdate(data.UID, data.Tokens)
			case "settings":
				settingsTGUpdate(data.UID, data.Settings)
			case "account":
				accountTGUpdate(data.UID, data.Account)
			}
		} else {
			switch data.Type {
			case "token":
				tokensUpdate(data.UID, data.Tokens)
			case "settings":
				settingsUpdate(data.UID, data.Settings)
			case "account":
				accountUpdate(data.UID, data.Account)
			}
		}
	case "remove":
		if data.IsTelegram {
			switch data.Type {
			case "sticker":
				response = templateTGRemove(tgStickers, data.UID, data.Template)
			}
		} else {
			switch data.Type {
			case "common":
				response = templateRemove(templateCommon, data.UID, data.Template)
			case "voice":
				response = templateRemove(templateVoice, data.UID, data.Template)
			case "dutys":
				response = templateRemove(templateDutys, data.UID, data.Template)
			case "anim":
				response = templateRemove(templateAnim, data.UID, data.Template)
			}
		}
	case "start":
		if data.IsTelegram {
			response = startTG()
		} else {
			response = start()
		}
	case "is_user":
		response = isUser(data.UID)
	case "add_user":
		if data.IsTelegram {
			addTgUser(data.UID)
		} else {
			addUser(data.UID)
		}
	case "remove_user":
		if data.IsTelegram {
			removeTgUser(data.UID)
		} else {
			removeUser(data.UID)
		}
	case "balance":
		switch data.Type {
		case "increase":
			balanceIncrease(data.UID, data.Value)
		case "decrease":
			balanceDecrease(data.UID, data.Value)
		case "set":
			balanceSet(data.UID, data.Value)
		case "get":
			response = balanceGet(data.UID)
		case "get_users":
			if data.IsTelegram {
				response = accountTGGetAll()
			} else {
				response = accountGetAll()
			}
		}
	case "die":
		quitSignal <- os.Interrupt
	case "info":
		switch data.Type {
		case "templates":
			response = templatesQuantity()
		}
	}
	fmt.Println(response)
	result, err := json.Marshal(resp{Response: response})
	if err != nil {
		panic(fmt.Sprint("response marshalling error: ", err))
	}
	_, err = c.Write(result)
	if err != nil {
		fmt.Println("connection writing error: ", err)
	}
}

func isUser(uid int) bool {
	var users []int
	var err error
	err = usersDB.Get("list", &users)
	if err != nil {
		panic(err)
	}
	return userExist(users, uid)
}

func userExist(users []int, user int) bool {
	for _, item := range users {
		if user == item {
			return true
		}
	}
	return false
}

func addUser(uid int) {
	var users []int
	var err error
	err = usersDB.Get("list", &users)
	if err != nil {
		panic(err)
	}
	if userExist(users, uid) {
		panic("User already exist")
	}
	createTemplatesFile(templateCommon, uid)
	createTemplatesFile(templateVoice, uid)
	createTemplatesFile(templateDutys, uid)
	createTemplatesFile(templateAnim, uid)
	err = settingsDB.Set(uid, settings{
		Nickname: "Здесь мог быть ваш ник",
		Prefix:   ".л ",
		Delete:   delSets{Deleter: "дд", Editor: "&#13;", EditCMD: true, OldType: true},
		Repeater: repeater{Prefix: ".."},
	})
	err = billing.Set(uid, float32(5))
	err = accounts.Set(uid, account{
		LocalID:        len(users),
		TimeJoin:       time.Now().Unix(),
		MergedAccounts: make([]int, 0),
		Achievements:   make([]string, 0),
	})
	err = tokenPool.Set(uid, tokens{})
	err = usersDB.Set("list", append(users, uid))
	if err != nil {
		panic(err)
	}
}

func removeUser(uid int) {
	var users []int
	var err error
	err = usersDB.Get("list", &users)
	if err != nil {
		panic(err)
	}
	if !userExist(users, uid) {
		panic("User not exist")
	}
	os.Remove(folder + templateCommon + strconv.Itoa(uid))
	os.Remove(folder + templateVoice + strconv.Itoa(uid))
	os.Remove(folder + templateAnim + strconv.Itoa(uid))
	os.Remove(folder + templateDutys + strconv.Itoa(uid))
	settingsDB.Delete(uid)
	billing.Delete(uid)
	accounts.Delete(uid)
	tokenPool.Delete(uid)
	for i, item := range users {
		if item == uid {
			if len(users) > 1 {
				if i < len(users)-1 {
					users = append(users[:i], users[i+1:]...)
				} else {
					users = users[:i]
				}
			} else {
				users = make([]int, 0)
			}

		}
	}
	err = usersDB.Set("list", users)
	if err != nil {
		panic(err)
	}
}

func start() []int {
	users := make([]int, 0)
	err := usersDB.Get("list", &users)
	if err != nil {
		if fmt.Sprint(err) == "Error: key not found" {
			users = make([]int, 0)
			usersDB.Set("list", users)
		} else {
			panic(fmt.Sprint("start error: ", err))
		}
	}
	os.Mkdir(folder+templateCommon, 0766)
	os.Mkdir(folder+templateAnim, 0766)
	os.Mkdir(folder+templateDutys, 0766)
	os.Mkdir(folder+templateVoice, 0766)
	fmt.Println(users)
	return users
}

func mainListen() interface{} {
	port := strconv.Itoa(50000)
	if len(os.Args) > 1 {
		port = os.Args[1]
	}
	ln, err := net.Listen("tcp", "localhost:"+port)
	if err != nil {
		log.Fatal("Listen error: ", err)
	}
	log.Println("DB server listening at port", clr.Colorize(port, clr.G))
	for {
		conn, err := ln.Accept()
		if err != nil {
			log.Fatal("Accept error: ", err)
		}
		go requestHandle(conn)
	}
}

func report(module string, message string) {
	fmt.Printf("DB report | %s: %s\n", module, message)
}

type tempQty struct {
	Common int `json:"common"`
	Voice  int `json:"voice"`
	Anim   int `json:"anim"`
}

func templatesQuantity() tempQty {
	var qty tempQty
	for _, user := range start() {
		qty.Common += len(templateGet(templateCommon, user))
		qty.Voice += len(templateGet(templateVoice, user))
		qty.Anim += len(templateGet(templateAnim, user))
	}
	return qty
}

type templateReq struct {
	Name     string `json:"name"`
	Category string `json:"category"`
	Text     string `json:"text"`

	ID          int64  `json:"id"`
	Attachments string `json:"attachments"`
	// сверху уникальные поля для вк, снизу для телеги
	Files []mediaFile `json:"files"`
}

type template struct {
	ID          int    `json:"id"`
	Name        string `json:"name"`
	Category    string `json:"category"`
	Text        string `json:"text"`
	Attachments string `json:"attachments"`
}

func templateRemove(catalog string, uid int, data templateReq) template {
	templates := make([]template, 0)
	var replacedTemplate template
	err := readTemplates(catalog, uid, &templates)
	if err != nil {
		report("TempRemove", fmt.Sprint("template read ", err))
	}
	for i, tmp := range templates {
		if strings.ToLower(tmp.Name) == strings.ToLower(data.Name) {
			replacedTemplate = tmp
			if len(templates) > 1 {
				if i < len(templates)-1 {
					templates = append(templates[:i], templates[i+1:]...)
				} else {
					templates = templates[:i]
				}
			} else {
				templates = make([]template, 0)
			}
		}
	}
	if err := writeTemplates(catalog, uid, templates); err != nil {
		panic(fmt.Sprint("template set ", err))
	}
	return replacedTemplate
}

func templateSet(catalog string, uid int, data templateReq) template {
	templates := make([]template, 0)
	var replacedTemplate template
	var exist bool
	err := readTemplates(catalog, uid, &templates)
	if err != nil {
		report("TempGet", fmt.Sprint("template read ", err))
	}
	newTemplate := template{
		Name:        data.Name,
		Attachments: data.Attachments,
		Text:        data.Text,
		Category:    data.Category,
	}
	for i, tmp := range templates {
		if tmp.Name == data.Name {
			templates[i] = newTemplate
			replacedTemplate = tmp
			exist = true
			break
		}
	}
	getID := func() int {
		id := 0
		for i, item := range templates {
			if id == item.ID {
				id = i + 1
			}
		}
		return id
	}
	if !exist {
		newTemplate.ID = getID()
		templates = append(templates, newTemplate)
	}
	if err := writeTemplates(catalog, uid, templates); err != nil {
		panic(fmt.Sprint("template set ", err))
	}
	return replacedTemplate
}

func templateGet(catalog string, uid int) []template {
	templates := make([]template, 0)
	readTemplates(catalog, uid, &templates)
	return templates
}

func balanceGet(uid int) float32 {
	var balance float32
	if err := billing.Get(uid, &balance); err != nil {
		panic(fmt.Sprint("balance get error:", err))
	}
	return balance
}

func balanceIncrease(uid int, value float32) {
	var balance float32
	if err := billing.Get(uid, &balance); err != nil {
		panic(fmt.Sprint("balance get error (increasing):", err))
	}
	balance += value
	if err := billing.Set(uid, balance); err != nil {
		panic(fmt.Sprint("balance get error (setting):", err))
	}
}

func balanceDecrease(uid int, value float32) {
	var balance float32
	if err := billing.Get(uid, &balance); err != nil {
		panic(fmt.Sprint("balance get error (decreasing):", err))
	}
	balance -= value
	if err := billing.Set(uid, balance); err != nil {
		panic(fmt.Sprint("balance get error (setting):", err))
	}
}

func balanceSet(uid int, balance float32) {
	if err := billing.Set(uid, balance); err != nil {
		panic(fmt.Sprint("balance get error (setting):", err))
	}
}

type farm struct {
	ON       bool    `json:"on"`
	Soft     bool    `json:"soft"`
	LastTime float32 `json:"last_time"`
}

type delSets struct {
	Deleter string `json:"deleter"`
	Editor  string `json:"editor"`
	EditCMD bool   `json:"editcmd"`
	OldType bool   `json:"old_type"`
}

type mentions struct {
	All  bool `json:"all"`
	Mine bool `json:"mine"`
}

type repeater struct {
	On     bool   `json:"on"`
	Prefix string `json:"prefix"`
}

type settings struct {
	Nickname         string   `json:"nickname"`
	Prefix           string   `json:"prefix"`
	FriendsAdd       bool     `json:"friends_add"`
	Farm             farm     `json:"farm"`
	DogsDel          bool     `json:"dogs_del"`
	DelRequests      bool     `json:"del_requests"`
	IgnoreList       []string `json:"ignore_list"`
	Online           bool     `json:"online"`
	Offline          bool     `json:"offline"`
	TemplatesBind    int      `json:"templates_bind"`
	TrustedUsers     []int    `json:"trusted_users"`
	Delete           delSets  `json:"delete"`
	Mentions         mentions `json:"mentions"`
	LeaveChats       bool     `json:"leave_chats"`
	Repeater         repeater `json:"repeater"`
	AutostatusOn     bool     `json:"autostatus_on"`
	AutostatusFormat string   `json:"autostatus_format"`
}

type settingsReq struct {
	Nickname         *string   `json:"nickname"`
	Prefix           *string   `json:"prefix"`
	FriendsAdd       *bool     `json:"friends_add"`
	Farm             *farm     `json:"farm"`
	DogsDel          *bool     `json:"dogs_del"`
	DelRequests      *bool     `json:"del_requests"`
	IgnoreList       *[]string `json:"ignore_list"`
	Online           *bool     `json:"online"`
	Offline          *bool     `json:"offline"`
	TemplatesBind    *int      `json:"templates_bind"`
	TrustedUsers     *[]int    `json:"trusted_users"`
	Delete           *delSets  `json:"delete"`
	Mentions         *mentions `json:"mentions"`
	LeaveChats       *bool     `json:"leave_chats"`
	Repeater         *repeater `json:"repeater"`
	AutostatusOn     *bool     `json:"autostatus_on"`
	AutostatusFormat *string   `json:"autostatus_format"`
}

func settingsUpdate(uid int, sets settingsReq) {
	var settings = settings{
		IgnoreList:   make([]string, 0),
		TrustedUsers: make([]int, 0)}
	if err := settingsDB.Get(uid, &settings); err != nil {
		report("settings(update)", clr.Colorize(fmt.Sprint("Error!", uid, "|", err), clr.R))
	}
	if sets.DelRequests != nil {
		settings.DelRequests = *sets.DelRequests
	}
	if sets.Delete != nil {
		settings.Delete = *sets.Delete
	}
	if sets.Farm != nil {
		settings.Farm = *sets.Farm
	}
	if sets.FriendsAdd != nil {
		settings.FriendsAdd = *sets.FriendsAdd
	}
	if sets.IgnoreList != nil {
		settings.IgnoreList = *sets.IgnoreList
	}
	if sets.Nickname != nil {
		settings.Nickname = *sets.Nickname
	}
	if sets.Offline != nil {
		settings.Offline = *sets.Offline
	}
	if sets.Online != nil {
		settings.Online = *sets.Online
	}
	if sets.Prefix != nil {
		settings.Prefix = *sets.Prefix
	}
	if sets.TemplatesBind != nil {
		settings.TemplatesBind = *sets.TemplatesBind
	}
	if sets.TrustedUsers != nil {
		settings.TrustedUsers = *sets.TrustedUsers
	}
	if sets.Mentions != nil {
		settings.Mentions = *sets.Mentions
	}
	if sets.LeaveChats != nil {
		settings.LeaveChats = *sets.LeaveChats
	}
	if sets.DogsDel != nil {
		settings.DogsDel = *sets.DogsDel
	}
	if sets.AutostatusFormat != nil {
		settings.AutostatusFormat = *sets.AutostatusFormat
	}
	if sets.Repeater != nil {
		settings.Repeater = *sets.Repeater
	}
	if sets.AutostatusOn != nil {
		settings.AutostatusOn = *sets.AutostatusOn
	}
	if err := settingsDB.Set(uid, settings); err != nil {
		panic(fmt.Sprint("settings update error:", err))
	}
}

func settingsGet(uid int) settings {
	var settings = settings{
		IgnoreList:   make([]string, 0),
		TrustedUsers: make([]int, 0)}
	if err := settingsDB.Get(uid, &settings); err != nil {
		report("settings(GET)", clr.Colorize(fmt.Sprint("Error!", uid, "|", err), clr.R))
	}
	return settings
}

type account struct {
	LocalID        int      `json:"local_id"`
	VkID           int      `json:"vk_id"`
	TgID           int      `json:"tg_id"`
	VKbind         int      `json:"vk_bind"`
	TimeJoin       int64    `json:"time_join"`
	Login          string   `json:"login"`
	Password       string   `json:"password"`
	Email          string   `json:"email"`
	Merged         bool     `json:"merged"`
	MergedAccounts []int    `json:"merged_accounts"`
	VkLongpoll     bool     `json:"vk_longpoll"`
	AddedBy        int      `json:"added_by"`
	Achievements   []string `json:"achievements"`
}

type accountReq struct {
	LocalID        *int      `json:"local_id"`
	VkID           *int      `json:"vk_id"`
	TgID           *int      `json:"tg_id"`
	TimeJoin       *int64    `json:"time_join"`
	Login          *string   `json:"login"`
	Password       *string   `json:"password"`
	Email          *string   `json:"email"`
	Merged         *bool     `json:"merged"`
	MergedAccounts *[]int    `json:"merged_accounts"`
	VkLongpoll     *bool     `json:"vk_longpoll"`
	TgBot          *bool     `json:"tg_bot"`
	Achievements   *[]string `json:"achievements"`
	AddedBy        *int      `json:"added_by"`
	On             *bool     `json:"on"`
	VKbind         *int      `json:"vk_bind"`
}

func accountUpdate(uid int, acc accountReq) {
	var curAcc = account{MergedAccounts: make([]int, 0), Achievements: make([]string, 0)}
	if err := accounts.Get(uid, &curAcc); err != nil {
		report("account(update)", clr.Colorize(fmt.Sprint("Read error!", uid, "|", err), clr.R))
	}
	if acc.Email != nil {
		curAcc.Email = *acc.Email
	}
	if acc.LocalID != nil {
		curAcc.LocalID = *acc.LocalID
	}
	if acc.VkID != nil {
		curAcc.VkID = *acc.VkID
	}
	if acc.TgID != nil {
		curAcc.TgID = *acc.TgID
	}
	if acc.VkLongpoll != nil {
		curAcc.VkLongpoll = *acc.VkLongpoll
	}
	if acc.Merged != nil {
		curAcc.Merged = *acc.Merged
	}
	if acc.MergedAccounts != nil {
		curAcc.MergedAccounts = *acc.MergedAccounts
	}
	if acc.TimeJoin != nil {
		curAcc.TimeJoin = *acc.TimeJoin
	}
	if acc.Password != nil {
		curAcc.Password = *acc.Password
	}
	if acc.Achievements != nil {
		curAcc.Achievements = *acc.Achievements
	}
	if acc.AddedBy != nil {
		curAcc.AddedBy = *acc.AddedBy
	}
	if err := accounts.Set(uid, curAcc); err != nil {
		panic(fmt.Sprint("account update error:", err))
	}
}

func accountGet(uid int) account {
	var account = account{MergedAccounts: make([]int, 0), Achievements: make([]string, 0)}
	if err := accounts.Get(uid, &account); err != nil {
		report("account(GET)", clr.Colorize(fmt.Sprint("Error!", uid, "|", err), clr.R))
	}
	return account
}

type accountsAll struct {
	UID     int     `json:"user_id"`
	Balance float32 `json:"balance"`
	account
}

func accountGetAll() []accountsAll {
	accounts := make([]accountsAll, 0)
	for _, user := range start() {
		accounts = append(accounts, accountsAll{UID: user,
			account: accountGet(user), Balance: balanceGet(user)})
	}
	return accounts
}

type tokensReq struct {
	MainVK   *string `json:"access_token"`
	MeVK     *string `json:"me_token"`
	OnlineVK *string `json:"online_token"`
	Session  *string `json:"session"`
}

type tokens struct {
	MainVK   string `json:"access_token"`
	MeVK     string `json:"me_token"`
	OnlineVK string `json:"online_token"`
}

func tokensUpdate(uid int, token tokensReq) error {
	var tokens tokens
	if err := tokenPool.Get(uid, &tokens); err != nil {
		report("tokens(update)", clr.Colorize(fmt.Sprint("Error!", uid, "|", err), clr.R))
	}
	if token.MainVK != nil {
		tokens.MainVK = *token.MainVK
	}
	if token.MeVK != nil {
		tokens.MeVK = *token.MeVK
	}
	if token.OnlineVK != nil {
		tokens.OnlineVK = *token.OnlineVK
	}
	return tokenPool.Set(uid, tokens)
}

func tokensGet(uid int) (token tokens) {
	if err := tokenPool.Get(uid, &token); err != nil {
		report("tokens(GET)", clr.Colorize(fmt.Sprint("Error!", uid, "|", err), clr.R))
	}
	return token
}

// ---------------------------------------------------- Телега ---------------------------------------------------- //

func startTG() []int {
	users := make([]int, 0)
	err := usersDB.Get("tglist", &users)
	if err != nil {
		if fmt.Sprint(err) == "Error: key not found" {
			users = make([]int, 0)
			usersDB.Set("tglist", users)
		} else {
			panic(fmt.Sprint("TG start error: ", err))
		}
	}
	os.Mkdir(folder+tgStickers, 0766)
	fmt.Println(users)
	return users
}

type accountsTGAll struct {
	UID int `json:"user_id"`
	// Balance float32 `json:"balance"`
	accountTG
}

func accountTGGetAll() []accountsTGAll {
	accounts := make([]accountsTGAll, 0)
	for _, user := range startTG() {
		accounts = append(accounts, accountsTGAll{UID: user,
			accountTG: accountTGGet(user)})
	}
	return accounts
}

func addTgUser(uid int) {
	var users []int
	var err error
	err = usersDB.Get("tglist", &users)
	if err != nil {
		panic(err)
	}
	if userExist(users, uid) {
		panic("User already exist")
	}
	createTemplatesFile(tgStickers, uid)
	err = settingsTgDB.Set(uid, settingsTG{
		Nickname: "Здесь мог быть ваш ник",
		Prefix:   ".л ",
		Editor:   "Handled with ❤️",
		Deleter:  "дд",
	})
	err = accountsTgDB.Set(uid, accountTG{})
	err = sessionTgDB.Set(uid, sessionTG{})
	err = usersDB.Set("tglist", append(users, uid))
	if err != nil {
		panic(err)
	}
}

func removeTgUser(uid int) {
	var users []int
	var err error
	err = usersDB.Get("tglist", &users)
	if err != nil {
		panic(err)
	}
	if !userExist(users, uid) {
		panic("User not exist")
	}
	os.Remove(folder + tgStickers + strconv.Itoa(uid))
	accountsTgDB.Delete(uid)
	settingsTgDB.Delete(uid)
	sessionTgDB.Delete(uid)
	for i, item := range users {
		if item == uid {
			if len(users) > 1 {
				if i < len(users)-1 {
					users = append(users[:i], users[i+1:]...)
				} else {
					users = users[:i]
				}
			} else {
				users = make([]int, 0)
			}
		}
	}
	err = usersDB.Set("tglist", users)
	if err != nil {
		panic(err)
	}
}

type sessionTG struct {
	Session string `json:"session"`
}

func sessionTGUpdate(uid int, session tokensReq) error {
	var ses sessionTG
	if err := sessionTgDB.Get(uid, &ses); err != nil {
		report("TG tokens(update)", clr.Colorize(fmt.Sprint("Error!", uid, "|", err), clr.R))
	}
	if session.Session != nil {
		ses.Session = *session.Session
	}
	return sessionTgDB.Set(uid, ses)
}

func sessionTGGet(uid int) (session sessionTG) {
	if err := sessionTgDB.Get(uid, &session); err != nil {
		report("TG tokens(GET)", clr.Colorize(fmt.Sprint("Error!", uid, "|", err), clr.R))
	}
	return session
}

type settingsTG struct {
	Nickname string `json:"nickname"`
	Prefix   string `json:"prefix"`
	Deleter  string `json:"deleter"`
	Editor   string `json:"editor"`
}

func settingsTGUpdate(uid int, sets settingsReq) {
	var settings = settingsTG{}
	if err := settingsTgDB.Get(uid, &settings); err != nil {
		report("settings(update)", clr.Colorize(fmt.Sprint("Error!", uid, "|", err), clr.R))
	}
	if sets.Nickname != nil {
		settings.Nickname = *sets.Nickname
	}
	if sets.Prefix != nil {
		settings.Prefix = *sets.Prefix
	}
	if err := settingsTgDB.Set(uid, settings); err != nil {
		panic(fmt.Sprint("settings update error:", err))
	}
}

func settingsTGGet(uid int) settingsTG {
	var settings = settingsTG{}
	if err := settingsTgDB.Get(uid, &settings); err != nil {
		report("settings(GET)", clr.Colorize(fmt.Sprint("Error!", uid, "|", err), clr.R))
	}
	return settings
}

type accountTG struct {
	On     bool `json:"on"`
	VKbind int  `json:"vk_bind"`
}

func accountTGUpdate(uid int, sets accountReq) {
	var acc = accountTG{}
	if err := accountsTgDB.Get(uid, &acc); err != nil {
		report("account (update)", clr.Colorize(fmt.Sprint("Error!", uid, "|", err), clr.R))
	}
	if sets.VKbind != nil {
		acc.VKbind = *sets.VKbind
	}
	if sets.On != nil {
		acc.On = *sets.On
	}
	if err := accountsTgDB.Set(uid, acc); err != nil {
		panic(fmt.Sprint("TG account update error:", err))
	}
}

func accountTGGet(uid int) accountTG {
	var acc = accountTG{}
	if err := accountsTgDB.Get(uid, &acc); err != nil {
		report("TG account(GET)", clr.Colorize(fmt.Sprint("Error!", uid, "|", err), clr.R))
	}
	return acc
}

type mediaFile struct {
	ID            int64  `json:"id"`
	AccessHash    string `json:"access_hash"`
	FileReference string `json:"file_reference"`
}

type templateTG struct {
	Name     string      `json:"name"`
	Category string      `json:"category"`
	Files    []mediaFile `json:"files"`
	Text     string      `json:"text"`
}

func templateTGSet(catalog string, uid int, data templateReq) templateTG {
	templates := make([]templateTG, 0)
	var replacedTemplate templateTG
	var exist bool
	err := readTemplates(catalog, uid, &templates)
	if err != nil {
		report("TGTempUpd", fmt.Sprint("template read ", err))
	}
	newTemplate := templateTG{
		Name:     data.Name,
		Category: data.Category,
		Files:    data.Files,
		Text:     data.Text,
	}
	for i, tmp := range templates {
		if tmp.Name == data.Name {
			templates[i] = newTemplate
			replacedTemplate = tmp
			exist = true
			break
		}
	}
	if !exist {
		templates = append(templates, newTemplate)
	}
	if err := writeTemplates(catalog, uid, templates); err != nil {
		panic(fmt.Sprint("TGTempUpd (save)", err))
	}
	return replacedTemplate
}

func templateTGRemove(catalog string, uid int, data templateReq) templateTG {
	templates := make([]templateTG, 0)
	var replacedTemplate templateTG
	err := readTemplates(catalog, uid, &templates)
	if err != nil {
		report("TGTempRemove", fmt.Sprint("template read ", err))
	}
	for i, tmp := range templates {
		if strings.ToLower(tmp.Name) == strings.ToLower(data.Name) {
			replacedTemplate = tmp
			if len(templates) > 1 {
				if i < len(templates)-1 {
					templates = append(templates[:i], templates[i+1:]...)
				} else {
					templates = templates[:i]
				}
			} else {
				templates = make([]templateTG, 0)
			}
		}
	}
	if err := writeTemplates(catalog, uid, templates); err != nil {
		panic(fmt.Sprint("TGTempRemove (save)", err))
	}
	return replacedTemplate
}

func templateTGGet(catalog string, uid int) []templateTG {
	templates := make([]templateTG, 0)
	readTemplates(catalog, uid, &templates)
	return templates
}

func refactor() {
	// новые поля также нужно добавить в обе структуры, в update метод и в add_user
	// ничего в самой бд обновлять как-будто бы не надо, но я все равно оставлю эту функцию
}
