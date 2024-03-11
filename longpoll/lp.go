package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"time"
)

type getServerResponse struct {
	Key       string `json:"key"`
	Server    string `json:"server"`
	Ts        uint32 `json:"ts"`
	ErrorCode int16  `json:"error_code"`
	ErrorMsg  string `json:"error_msg"`
}

type vkResp struct {
	Response map[string]interface{} `json:"response"`
	Error    map[string]interface{} `json:"error"`
}

type message struct {
	Out int `json:"out"`
	ID  int `json:"id"`
}

type vkGSResp struct {
	Response getServerResponse `json:"response"`
	Error    getServerResponse `json:"error"`
}

type catchIncoming struct {
	Method       string
	UID          int
	Token        string
	Prefix       string
	Ignore       []string `json:"ignore_list"`
	Delete       delSets  `json:"delete"`
	Mentions     mentions `json:"mentions"`
	LeaveChats   bool     `json:"leave_chats"`
	TrustedUsers []int    `json:"trusted_users"`
	Repeater     repeater `json:"repeater"`
	Addr         string   `json:"addr"`
}

type repeater struct {
	On     bool   `json:"on"`
	Prefix string `json:"prefix"`
}

type mentions struct {
	All  bool `json:"all"`
	Mine bool `json:"mine"`
}

type delSets struct {
	Deleter string `json:"deleter"`
	Editor  string `json:"editor"`
	EditCMD bool   `json:"editcmd"`
	OldType bool   `json:"old_type"`
}

type errSend struct {
	Type string `json:"type"`
	UID  int    `json:"uid"`
}

type update struct {
	Type         float64                `json:"type"`
	ID           uint64                 `json:"id"`
	Mask         uint32                 `json:"mask"`
	PeerID       int                    `json:"peer_id"`
	Time         uint32                 `json:"time"`
	Text         string                 `json:"text"`
	ReceivedTime float64                `json:"received_time"`
	UID          int                    `json:"uid"`
	Attachments  map[string]interface{} `json:"attachments"`
}

type typeLPResp struct {
	TS      uint32          `json:"ts"`
	Updates [][]interface{} `json:"updates"`
	Failed  uint8           `json:"failed"`
}

type lpUser struct {
	id  uint32
	qty uint8
}

type info struct {
	Events   uint64 `json:"events"`
	Messages uint64 `json:"messages"`
	Seconds  uint64 `json:"seconds"`
	Commands uint64 `json:"commands"`
}

var addrUNIX string
var addrHTTP string
var overHTTP bool

var eventCounter uint64
var messageCounter uint64
var commandCounter uint64
var seconds uint64 = 60

var users map[int]lpUser
var isCopying map[int]bool
var eventCopyServer string

var ddRegular *regexp.Regexp
var ddEditRegular *regexp.Regexp
var allMentRegular *regexp.Regexp

func main() {
	ddRegular = regexp.MustCompile(`\d+`)
	ddEditRegular = regexp.MustCompile(`-( ?\d+)?(.+)?`)
	allMentRegular = regexp.MustCompile(`[*@](all|here|online|everyone|все|онлайн|здесь|тут)`)
	users = make(map[int]lpUser)
	isCopying = make(map[int]bool)
	addrUNIX, _ = filepath.Abs(filepath.Dir(os.Args[0]))
	addrUNIX = filepath.Join(addrUNIX, "catcher.sock")
	die := make(chan bool)
	go mainListen(die)
	go counter()
	<-die
}

func counter() {
	time.Sleep(60 * time.Second)
	for {
		fmt.Printf("\x1b[4mПриемник работает \x1b[32m%d\x1b[37m минут, за это время получено \x1b[32m%d\x1b[37m событий | \x1b[32m%d\x1b[37m событий в секунду\x1b[0m\n", seconds/60, eventCounter, eventCounter/seconds)
		seconds += 60
		time.Sleep(60 * time.Second)
	}
}

func incomingHandle(c net.Conn, die chan bool) {
	defer c.Close()
	buf := make([]byte, 8192)
	nr, err := c.Read(buf)
	if err != nil {
		return
	}
	var response interface{} = "\"ok\""
	var data catchIncoming
	json.Unmarshal(buf[0:nr], &data)
	switch data.Method {
	case "spawn":
		fmt.Println("------------------------SPAWNED------------------------")
		fmt.Println(data)
		if _, exist := users[data.UID]; !exist {
			tempUsers := users[data.UID]
			tempUsers.qty = 0
			users[data.UID] = tempUsers
		}
		go lpListen(data.Token, data.UID, data.Prefix,
			data.Ignore, data.Delete, data.Mentions,
			data.LeaveChats, data.TrustedUsers, data.Repeater)
	case "kill":
		if _, run := users[data.UID]; run {
			tempUsers := users[data.UID]
			tempUsers.qty = 0
			users[data.UID] = tempUsers
		}
	case "check":
		response = false
		if users, run := users[data.UID]; run {
			if users.qty > 0 {
				response = true
			}
		}
	case "start_copy_server":
		eventCopyServer = data.Addr
	case "copy_events":
		isCopying[data.UID] = true
	case "die":
		die <- true
	case "over_http":
		addrHTTP = data.Addr
		overHTTP = true
	case "info":
		info := info{
			Seconds:  seconds,
			Events:   eventCounter,
			Messages: messageCounter,
			Commands: commandCounter,
		}
		response = info
	}
	jsnd, _ := json.Marshal(response)
	c.Write(jsnd)
}

func mainListen(die chan bool) {
	log.Println("Starting catcher")
	ln, err := net.Listen("tcp", "localhost:"+string(os.Args[1]))
	if err != nil {
		log.Fatal("Listen error: ", err)
	}
	for {
		conn, err := ln.Accept()
		if err != nil {
			log.Fatal("Accept error: ", err)
		}
		go incomingHandle(conn, die)
	}
}

func unixSend(data []byte) {
	log.Println("Отправляю сигнал")
	if overHTTP {
		conn, err := net.Dial("tcp", addrHTTP)
		if err != nil {
			panic(fmt.Sprint("Dial error: ", err))
		}
		defer conn.Close()
		_, err = conn.Write(data)
		if err != nil {
			panic(fmt.Sprint("Send error: ", err))
		}
	} else {
		file, err := net.Dial("unixgram", addrUNIX)
		if err != nil {
			panic(fmt.Sprint("Dial error: ", err))
		}
		defer file.Close()
		_, err = file.Write(data)
		if err != nil {
			panic(fmt.Sprint("Send error: ", err))
		}
	}

}

func sendErr(typ string, uid int) {
	data, _ := json.Marshal(errSend{Type: typ, UID: uid})
	unixSend(data)
}

func send(uid int, update update, token string) (success bool) {
	defer func() {
		if err := recover(); err != nil {
			success = false
		}
	}()
	commandCounter++
	update.UID = uid
	data, err := json.Marshal(update)
	if err == nil {
		unixSend(data)
	}
	return true
}

func troublesNotify(update update, token string, text string) {
	query := url.Values{}
	query.Add("peer_id", strconv.Itoa(update.PeerID))
	query.Add("message", text)
	query.Add("message_id", fmt.Sprintf("%d", update.ID))
	vkMethod(token, "messages.edit", query.Encode())
}

func lpListen(token string, uid int, prefix string, iList []string,
	delSets delSets, mentions mentions, leaveChats bool,
	trustedUsers []int, repeater repeater) {
	defer func() {
		if err := recover(); err != nil {
			fmt.Println("User's death: ", err)
		}
	}()
	resp, errVk := getServer(token)
	if errVk {
		if resp.ErrorCode == 5 {
			sendErr("tokenfail", uid)
		} else {
			sendErr("failstart", uid)
		}
		return
	}
	var tList []string
	for _, user := range trustedUsers {
		tList = append(tList, strconv.Itoa(user))
	}
	tempUsers := users[uid]
	tempUsers.qty++
	tempUsers.id++
	localID := tempUsers.id
	users[uid] = tempUsers
	if _, exist := isCopying[uid]; !exist {
		isCopying[uid] = false
	}
	uidStringed := strconv.Itoa(int(uid))
	delEditor := fmt.Sprintf("%s-", delSets.Deleter)
	allCmd := []string{fmt.Sprintf("%sвсе", delSets.Deleter), fmt.Sprintf("%s-все", delSets.Deleter)}
	mention := fmt.Sprintf("[id%d|", uid)
	settingsInfoGet := func() string {
		return fmt.Sprintf("⚠ Приемник сигналов работает в аварийном режиме\n"+
			"Настройки, сохраненные на стороне LP модуля:\n"+
			"🚯 Удаление пушей всех: %t\n"+
			"🚯 Удаление пушей меня: %t\n"+
			"📯 Повторялка: %t, префикс: \"%s\"\n"+
			"🙅‍♀ Автовыход из бесед: %t\n\n"+
			"Удалялка: \"%s\", редактируется на \"%s\"",
			mentions.All, mentions.Mine, repeater.On, repeater.Prefix,
			leaveChats, delSets.Deleter, delSets.Editor)
	}
	for {
		var lpResp []update
		var err int8
		lpResp, resp.Ts, err = lpCheck(resp, uid)
		if err != 0 {
			fmt.Println(uid, err, resp.Ts)
			if err == 2 {
				newResp, errVk := getServer(token)
				resp.Key = newResp.Key
				resp.Server = newResp.Server
				resp.Ts = newResp.Ts
				err = 0
				fmt.Println(uid, newResp, resp.Ts)
				if resp.Ts == 0 {
					sendErr("failstart", uid)
					return
				}
				if errVk {
					if resp.ErrorCode == 5 {
						sendErr("tokenfail", uid)
						return
					}
					sendErr(newResp.ErrorMsg, uid)
					return
				}
			}
		}
		for _, update := range lpResp {
			messageCounter++
			if update.Mask&2 == 2 || update.PeerID == uid {
				if users[uid].qty != 1 {
					if users[uid].qty > 1 && users[uid].id > localID {
						tempUsers := users[uid]
						tempUsers.qty--
						users[uid] = tempUsers
						return
					} else if users[uid].qty == 0 {
						sendErr("dying", uid)
						return
					}
				}
				update.Text = strings.ToLower(update.Text)
				if strings.HasPrefix(update.Text, "!!") {
					update.Type = 444
					send(uid, update, token)
				} else if strings.HasPrefix(update.Text, "нд") {
					update.Type = 555
					if !send(uid, update, token) {
						troublesNotify(update, token, settingsInfoGet())
					}
				} else if strings.HasPrefix(update.Text, delEditor) {
					ddEdit(update, token, delSets.EditCMD, delSets.Editor, delSets.OldType, allCmd[1])
				} else if strings.HasPrefix(update.Text, delSets.Deleter) {
					dd(update, token, allCmd[0])
				} else if strings.HasSuffix(update.Text, "//") {
					messageDelete(token, update.ID, 1)
				} else if strings.HasPrefix(update.Text, "рр ") {
					pp(update, token)
				} else if strings.HasPrefix(update.Text, prefix) {
					update.Text = strings.Replace(update.Text, prefix, "", 1)
					if !send(uid, update, token) {
						troublesNotify(update, token,
							"⚠ Приемник сигналов работает в аварийном режиме "+
								"(автор где-то накосячил, напиши [id332619272|ему])")
					}
				}
			} else {
				if 0 < update.PeerID && len(iList) > 0 {
					if update.PeerID > 2000000000 {
						cid := update.Attachments["from"]
						if cid != nil {
							for _, iid := range iList {
								if iid == cid {
									messageDelete(token, update.ID, 0)
								}
							}
						}
					} else {
						for _, iid := range iList {
							if iid == strconv.Itoa(update.PeerID) {
								messageDelete(token, update.ID, 0)
							}
						}
					}
				}
				if mentions.Mine {
					if strings.Contains(update.Text, mention) {
						messageDelete(token, update.ID, 0)
					}
				}
				if mentions.All {
					if allMentRegular.MatchString(update.Text) {
						messageDelete(token, update.ID, 0)
					}
				}
				if leaveChats {
					if act, exist := update.Attachments["source_act"]; exist {
						getOut := false
						if act.(string) == "chat_create" {
							getOut = true
						} else if act.(string) == "chat_invite_user" {
							if mid, exist := update.Attachments["source_mid"]; exist {
								if mid.(string) == uidStringed {
									getOut = true
								}
							}
						}
						if getOut {
							vkMethod(token, "messages.removeChatUser",
								fmt.Sprintf("chat_id=%d&member_id=%d", update.PeerID-2e9, uid))
						}
					}
				}
				if repeater.On {
					if update.PeerID > 2000000000 {
						cid := update.Attachments["from"]
						if cid != nil {
							func() {
								for _, iid := range tList {
									if iid == cid {
										if strings.HasPrefix(strings.ToLower(update.Text), repeater.Prefix) {
											query := url.Values{}
											query.Add("peer_id", strconv.Itoa(update.PeerID))
											query.Add("message", strings.Replace(update.Text, repeater.Prefix, "", 1))
											query.Add("random_id", "0")
											vkMethod(token, "messages.send", query.Encode())
											return
										}
									}
								}
							}()
						}
					}
				}
			}
		}
	}
}

type updatesPack struct {
	Updates [][]interface{} `json:"updates"`
	UID     int             `json:"uid"`
}

func sendUpdates(uid int, updates [][]interface{}) {
	data, _ := json.Marshal(updatesPack{Updates: updates, UID: uid})
	conn, err := net.Dial("tcp", eventCopyServer)
	if err != nil {
		fmt.Println("Dial error: ", err)
		isCopying[uid] = false
	}
	defer conn.Close()
	_, err = conn.Write(data)
	if err != nil {
		panic(fmt.Sprint("Send error: ", err))
	}
	var response string
	json.NewDecoder(conn).Decode(&response)
	if response == "stop" {
		isCopying[uid] = false
	}
}

func lpCheck(resp getServerResponse, uid int) (updates []update, ts uint32, errLP int8) {
	var Updates []update
	var lpResp typeLPResp
	response, err := http.Get(fmt.Sprintf("https://%s?act=a_check&key=%s&ts=%d&wait=25&mode=2&version=3", resp.Server, resp.Key, resp.Ts))
	if err != nil {
		return Updates, lpResp.TS, 1
	}
	defer response.Body.Close()
	json.NewDecoder(response.Body).Decode(&lpResp)
	if lpResp.Failed != 0 {
		switch lpResp.Failed {
		case 1:
			return Updates, lpResp.TS, 0
		case 2:
			return Updates, lpResp.TS, 2
		case 3:
			return Updates, lpResp.TS, 2
		}
	} else {
		if isCopying[uid] {
			go sendUpdates(uid, lpResp.Updates)
		}
		for _, value := range lpResp.Updates {
			eventCounter++
			var curUpdate update
			for i, val := range value {
				if i == 0 {
					curUpdate.Type = val.(float64)
					if curUpdate.Type != 4 {
						break
					}
					curUpdate.ReceivedTime = float64(time.Now().UnixNano()) / 1000000000
				}
				switch i {
				case 1:
					curUpdate.ID = uint64(val.(float64))
				case 2:
					curUpdate.Mask = uint32(val.(float64))
				case 3:
					curUpdate.PeerID = int(val.(float64))
				case 4:
					curUpdate.Time = uint32(val.(float64))
				case 5:
					curUpdate.Text = val.(string)
				case 6:
					curUpdate.Attachments = val.(map[string]interface{})
					Updates = append(Updates, curUpdate)
				}
			}
		}
	}
	return Updates, lpResp.TS, 0
}

// ---------------------------------------------------- VK requests ---------------------------------------------------- //

func messageDelete(token string, msgID uint64, dfa int8) {
	resp, _ := http.Get(fmt.Sprintf("https://api.vk.com/method/messages.delete?v=5.110&access_token=%s&lang=ru&message_ids=%d&delete_for_all=%d",
		token, msgID, dfa))
	resp.Body.Close()
	return
}

func getServer(token string) (data getServerResponse, errVk bool) {
	var dat vkGSResp
	resp, err := http.Get(fmt.Sprintf("https://api.vk.com/method/messages.getLongPollServer?v=5.110&access_token=%s&lang=ru", token))
	if err != nil {
		return dat.Error, true
	}
	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	json.Unmarshal(body, &dat)
	fmt.Println(dat)
	if dat.Error.ErrorCode != 0 {
		return dat.Error, true
	}
	return dat.Response, false
}

func vkMethod(token string, method string, query string) (data map[string]interface{}, errCode float64) {
	var dat vkResp
	resp, err := http.Get(fmt.Sprintf("https://api.vk.com/method/%s?v=5.110&access_token=%s&lang=ru&%s", method, token, query))
	if err != nil {
		return
	}
	defer resp.Body.Close()
	body, _ := ioutil.ReadAll(resp.Body)
	json.Unmarshal(body, &dat)
	if dat.Error["error_code"] != nil {
		fmt.Println(dat)
		return dat.Error, dat.Error["error_code"].(float64)
	}
	return dat.Response, 0
}

// ----------------------------------------- deleters ----------------------------------------- //

func ddEdit(update update, token string, editCMD bool, editor string, old bool, allCmd string) {
	commandCounter++
	var count int

	countStr := ddEditRegular.FindStringSubmatch(update.Text)

	if update.Text == allCmd {
		count = 200
	} else if len(countStr) == 0 {
		count = 2
	} else {
		if countStr[2] != "" {
			editor = countStr[2]
		}
		count, _ = strconv.Atoi(countStr[1])
		if count < 2 {
			count = 2
		} else {
			count++
		}
	}

	if old {
		var msgList []string

		func() {
			defer func() { recover() }()
			i := 0
			messages, _ := vkMethod(token, "messages.getHistory",
				fmt.Sprintf("peer_id=%d&count=200", update.PeerID))
			for _, msg := range messages["items"].([]interface{}) {
				if msg.(map[string]interface{})["out"].(float64) == 1 {
					msgID := fmt.Sprintf("%f", msg.(map[string]interface{})["id"].(float64))
					msgList = append(msgList, msgID)
					if !editCMD {
						if i == 0 {
							i++
							continue
						}
					}
					query := url.Values{}
					query.Add("peer_id", strconv.Itoa(update.PeerID))
					query.Add("message", editor)
					query.Add("message_id", msgID)
					_, err := vkMethod(token, "messages.edit", query.Encode())
					if err == 14 || err == 909 {
						break
					}
					if (4 > count && count > 2 && editCMD) || (5 > count && count > 3 && !editCMD) {
						time.Sleep(300 * time.Millisecond)
					} else if count > 3 && count <= 10 {
						time.Sleep(500 * time.Millisecond)
					} else if count > 10 {
						time.Sleep(1 * time.Second)
					}
					i++
					if i == count {
						break
					}
				}
			}
		}()

		var msgsFormatted string
		for i, id := range msgList {
			if i == 0 {
				msgsFormatted += id
			} else {
				msgsFormatted += "," + id
			}
		}

		retry := 0
		for retry < 5 {
			_, err := vkMethod(token, "messages.delete",
				"message_ids="+msgsFormatted+"&delete_for_all=1")
			if err == 6 {
				time.Sleep(time.Millisecond * 300)
				retry++
				continue
			}
			break
		}

	} else {
		var err float64
		func() {
			defer func() { recover() }()
			i := 0
			messages, _ := vkMethod(token, "messages.getHistory",
				fmt.Sprintf("peer_id=%d&count=200", update.PeerID))
			for _, msg := range messages["items"].([]interface{}) {
				if msg.(map[string]interface{})["out"].(float64) == 1 {
					msgID := msg.(map[string]interface{})["id"].(float64)
					if !editCMD && i == 0 {
						vkMethod(token, "messages.delete",
							"message_ids="+fmt.Sprintf("%f", msgID)+"&delete_for_all=1")
						i++
						continue
					}
					if err != 14 {
						execute := fmt.Sprintf(`API.messages.edit({"peer_id":%d,"message":"%s","message_id":%f});`+
							`API.messages.delete({"message_ids":%f,"delete_for_all":1});`, update.PeerID, editor, msgID, msgID)
						_, err = vkMethod(token, "execute", "code="+url.QueryEscape(execute))
					}
					if err == 14 {
						vkMethod(token, "messages.delete",
							"message_ids="+
								strconv.FormatFloat(msg.(map[string]interface{})["id"].(float64), 'f', 0, 32)+
								"&delete_for_all=1")
					} else if err != 0 {
						break
					}
					if err == 14 || err == 920 {
						i++
						continue
					}
					if (4 > count && count > 2 && editCMD) || (5 > count && count > 3 && !editCMD) {
						time.Sleep(300 * time.Millisecond)
					} else if count > 3 && count <= 10 {
						time.Sleep(500 * time.Millisecond)
					} else if count > 10 {
						time.Sleep(1 * time.Second)
					}
					i++
					fmt.Println(i, count, countStr, err)
					if i == count {
						break
					}
				}
			}
		}()
	}
}

func dd(update update, token string, allCmd string) {
	commandCounter++
	var count int

	countStr := ddRegular.FindString(update.Text)

	if update.Text == allCmd {
		count = 1000
	} else if countStr == "" {
		count = 2
	} else {
		count, _ = strconv.Atoi(countStr)
		count++
	}

	code := fmt.Sprintf(`
	var i = 0;
	var msg_ids = [];
	var count = %d;
	var items = API.messages.getHistory({"peer_id":%d,"count":"200", "offset":"0"}).items;
	while (count > 0 && i < items.length) {
	    if (items[i].out == 1) {
			if (items[i].id == %d) {
				if (items[i].reply_message) {
					msg_ids.push(items[i].id);
					msg_ids.push(items[i].reply_message.id);
					count = 0;
				};
				if (items[i].fwd_messages) {
					msg_ids.push(items[i].id);
					var j = 0;
					while (j < items[i].fwd_messages.length) {
						msg_ids.push(items[i].fwd_messages[j].id);
						j = j + 1;
					};
					count = 0;
				};
			};
	        msg_ids.push(items[i].id);
	        count = count - 1;
	        };
	    if ((%d - items[i].date) > 86400) {count = 0;};
	    i = i + 1;
	};
	API.messages.delete({"message_ids": msg_ids,"delete_for_all":"1"});
	return count;`, count, update.PeerID, update.ID, update.Time)
	vkMethod(token, "execute", fmt.Sprintf("code=%s", url.QueryEscape(code)))
}

func pp(update update, token string) {
	commandCounter++
	code := fmt.Sprintf(`
    var i = 0;
    var l = 0;
    var atts = [];
    var cmd_msg = {};
    var msgs = API.messages.getHistory({"peer_id":%d}).items;
    var msg_id = 0;

    while (i < 200){
        if (msgs[i].out == 1) {
            if (l == 0) {
                cmd_msg = {"text": msgs[i].text, "id": msgs[i].id,
                "attachments": msgs[i].attachments};
                if (msgs[i].reply_message) {
                    msg_id = msgs[i].reply_message.id;
                };
            };
            if (l == 1 && msg_id == 0) {
                msg_id = msgs[i].id;
            };
            if (l == 2) { i = 200; };
            l = l + 1;
        };
        i = i + 1;
    };
    if (cmd_msg.attachments) {
        i = 0;
        while ( i < cmd_msg.attachments.length) {
            var type = cmd_msg.attachments[i].type;
            if (type != "link") {
            atts.push(type + cmd_msg.attachments[i][type].owner_id +
            "_" + cmd_msg.attachments[i][type].id);
            };
            i = i + 1;
        };
    };
    API.messages.edit({
        "peer_id": %d,"message_id": msg_id,
        "message": cmd_msg.text.substr(4, 10000),
        "attachment": atts,
        "keep_forward_messages": 1
        });
    API.messages.delete({"message_ids": cmd_msg.id, "delete_for_all":"1"});
    return 1;`, update.PeerID, update.PeerID)
	url := fmt.Sprintf("https://api.vk.com/method/execute?v=5.110&access_token=%s&lang=ru&code=%s", token, url.QueryEscape(code))
	resp, er := http.Get(url)
	if er != nil {
		fmt.Println("Ошибка: ", er)
		return
	}
	resp.Body.Close()
	return
}
