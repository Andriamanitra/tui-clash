require "socket"
require "json"
require "log"

# TODO: this should be customizable via command line parameter
MAX_MSG_SIZE = 20_000

class Submission
  include JSON::Serializable
  property author : String
  property command : String
  property code : String
  property time : String?
end

module TuiClashServer
  PUZZLE_PATHS = Dir.glob("clashes/*.json")
  @@current_puzzle_path : String? = nil
  @@current_puzzle = ""
  @@submissions = [] of Submission
  @@players = [] of Player

  def self.puzzle_msg
    "PUZZLE:#{@@current_puzzle}"
  end

  def self.submission_msg
    "SUBMISSIONS:#{@@submissions.to_json}"
  end

  def self.change_puzzle
    end_round unless @@current_puzzle_path.nil?
    puzzle_path = PUZZLE_PATHS.sample
    @@current_puzzle = File.read(puzzle_path)
    @@current_puzzle_path = puzzle_path
    @@submissions.clear
    puzzle = puzzle_msg()
    @@players.each(&.send puzzle)
    Log.debug { "Puzzle changed to #{@@current_puzzle_path}" }
  end

  def self.end_round
    @@current_puzzle_path = nil
    @@current_puzzle = ""
    msg = submission_msg()
    @@players.each(&.send msg)
    Log.info { "Round ended" }
  end

  def self.add_submission(submission : Submission)
    @@submissions << submission
  end

  def self.add_player(player : Player)
    msg = puzzle_msg
    player.send(msg) unless msg.empty?
    @@players << player
    Log.info { "#{player} connected" }
  end

  def self.disconnect(player : Player)
    Log.info { "#{player} disconnected" }
    @@players.delete(player)
  end

  class Player
    @@id = 0
    @sock : TCPSocket
    @id : Int32

    def initialize(socket : TCPSocket)
      @sock = socket
      @id = @@id
      @@id += 1
      TuiClashServer.add_player(self)
    end

    def send(msg : String)
      @sock.write_bytes(msg.bytesize, IO::ByteFormat::LittleEndian)
      @sock << msg
    end

    def listen
      loop do
        msg_size = @sock.read_bytes(UInt32, IO::ByteFormat::LittleEndian)
        if msg_size > MAX_MSG_SIZE
          raise Exception.new("message too long (size=#{msg_size})")
        end
        msg = @sock.read_string(msg_size)
        handle(msg.strip)
      end
    rescue ex
      Log.debug { "#{self} disconnected due to '#{ex}'" }
      TuiClashServer.disconnect(self)
      @sock.close
    end

    def handle(msg : String)
      Log.debug { "Received message from #{self} : '#{msg}'" }
      case msg
      when "END ROUND"
        TuiClashServer.end_round
      when "START ROUND"
        TuiClashServer.change_puzzle
      when .starts_with?("SUBMISSION:")
        submission_body = msg.lchop("SUBMISSION:")
        submit(submission_body)
      else
        Log.warn { "UNRECOGNIZED MESSAGE FROM #{self}: '#{msg}'" }
      end
    end

    def submit(subm : String)
      submission = Submission.from_json(subm)
      submission.time = Time.utc.to_s
      TuiClashServer.add_submission(submission)
      Log.info { "Accepted submission from #{submission.author} (#{self})" }
      send "ACCEPTED"
    rescue JSON::ParseException
      send "DENIED"
    rescue ex : JSON::SerializableError
      send "DENIED"
    end

    def to_s(io : IO)
      io << "Player #{@id}"
    end
  end

  Log.setup(:debug)
  server = TCPServer.new("0.0.0.0", 1335)
  Log.info { "listening on 0.0.0.0:1335" }
  while client = server.accept?
    spawn Player.new(client).listen
  end
end
