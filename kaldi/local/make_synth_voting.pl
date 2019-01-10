#!/usr/bin/perl
# Prepare data (Puiblic dataset association result) for fine_tuning


if (@ARGV != 2) {
  print STDERR "Usage: $0 <path-to-synth> <path-to-data-dir>\n";
  print STDERR "e.g. $0 /export/synth_voting data/synth_voting\n";
  exit(1);
}

# Check that ffmpeg is installed.
if (`which ffmpeg` eq "") {
  die "Error: this script requires that ffmpeg is installed.";
}

($data_base, $out_dir) = @ARGV;

opendir my $dh, "$data_base" or die "Cannot open directory: $!";
my @spkr_dirs = grep {-d "$data_base/$_" && ! /^\.{1,2}$/} readdir($dh);
closedir $dh;

if (! -d "$out_dir") {
  mkdir($out_dir) or die "Could not create directory $!";
}
open(SPKR, ">", "$out_dir/utt2spk") or die "Could not open the output file $out_dir/utt2spk";
open(WAV, ">", "$out_dir/wav.scp") or die "Could not open the output file $out_dir/wav.scp";

foreach (@spkr_dirs) {
  my $spkr_id = $_;
  opendir my $dh, "$data_base/$spkr_id/" or die "Cannot open directory: $!";
  my @files = map{s/\.[^.]+$//;$_}grep {/\.m4a$/} readdir($dh);
  closedir $dh;

  foreach (@files) {
    my $name = $_;
    my $wav = "ffmpeg -v 8 -i $data_base/$spkr_id/$name.m4a -f wav -acodec pcm_s16le -|";
    my $utt_id = "$spkr_id-$name";
    print WAV "$utt_id", " $wav", "\n";
    print SPKR "$utt_id", " $spkr_id", "\n";
  }
}

close(SPKR) or die;
close(WAV) or die;

if (system(
  "utils/utt2spk_to_spk2utt.pl $out_dir/utt2spk >$out_dir/spk2utt") != 0) {
  die "Error creating spk2utt file in directory $out_dir";
}
system("env LC_COLLATE=C utils/fix_data_dir.sh $out_dir");
if (system("env LC_COLLATE=C utils/validate_data_dir.sh --no-text --no-feats $out_dir") != 0) {
  die "Error validating directory $out_dir";
}
